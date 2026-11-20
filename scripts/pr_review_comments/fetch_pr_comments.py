#!/usr/bin/env python3
"""Collect the review feedback received on my GitHub PRs into a local file.

The `niche-review` agent skill (pos-agent-kit/skills/niche-review)
reads the output so that new code is reviewed against the comments I keep
getting, without hitting GitHub on every review.

Run it from time to time:

    python3 fetch_pr_comments.py            # incremental (only PRs updated since last run)
    python3 fetch_pr_comments.py --full     # refetch everything
    python3 fetch_pr_comments.py --since 2025-01-01

Token: GITHUB_TOKEN / GH_TOKEN from the environment, otherwise the
GITHUB_TOKEN line of $POS_KIT_ENV_FILE, defaulting to the project root's
.env (the directory that contains pos-agent-kit/). Read-only, stdlib only.

Output (next to this script, in data/):
  comments.json       raw store, one entry per PR with every feedback item
  review_comments.md  digest grouped by file, with the diff hunk of each
                      inline comment and the reply thread
  review_comments_compact.md  same, keeping only the last lines of each hunk
                      (the lines the comment is anchored to)
  python3 fetch_pr_comments.py --render-only   rebuilds the .md files offline
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.github.com"
HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "data"
DEFAULT_REPOS = ("odoo/odoo", "odoo/enterprise", "odoo/upgrade")
# pos-agent-kit/scripts/pr_review_comments/ -> project root is three levels up.
ENV_FILE = Path(os.environ.get("POS_KIT_ENV_FILE") or HERE.parents[2] / ".env")
# Accounts whose messages are status/automation, not review feedback.
IGNORED_USERS = {
    "robodoo", "fw-bot", "c3pobot", "c3podoo", "odoo-github-bot", "github-actions",
    "copilot", "copilot-pull-request-reviewer", "odoo-translate",
}
HUNK_TAIL = 40  # lines of diff hunk kept in the markdown digest
COMPACT_HUNK = 6  # ... and in the compact digest


# ---------------------------------------------------------------- GitHub I/O

def load_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?GITHUB_TOKEN\s*=\s*(.+)", line)
            if m:
                return m.group(1).strip().strip("'\"")
    sys.exit("No GitHub token: set GITHUB_TOKEN or add it to %s" % ENV_FILE)


class GitHub:
    def __init__(self, token):
        self.headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pr-review-comments-fetcher",
        }

    def _get(self, url):
        for attempt in range(5):
            req = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.load(resp), resp.headers.get("Link", "")
            except urllib.error.HTTPError as e:
                remaining = e.headers.get("X-RateLimit-Remaining")
                if e.code in (403, 429) and (remaining == "0" or e.headers.get("Retry-After")):
                    reset = int(e.headers.get("X-RateLimit-Reset", time.time() + 60))
                    wait = int(e.headers.get("Retry-After") or max(reset - time.time(), 1)) + 1
                    print(f"  rate limited, sleeping {wait}s", file=sys.stderr)
                    time.sleep(min(wait, 900))
                    continue
                if e.code >= 500 and attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise SystemExit(f"GitHub {e.code} on {url}: {e.read()[:300]!r}")
            except urllib.error.URLError:
                if attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise SystemExit(f"Giving up on {url}")

    def get(self, path, **params):
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return self._get(url)[0]

    def paginate(self, path, **params):
        params.setdefault("per_page", 100)
        url = API + path + "?" + urllib.parse.urlencode(params)
        while url:
            data, link = self._get(url)
            yield from (data["items"] if isinstance(data, dict) else data)
            m = re.search(r'<([^>]+)>;\s*rel="next"', link)
            url = m.group(1) if m else None


# ---------------------------------------------------------------- collection

def is_noise(user, body):
    if not body or not body.strip():
        return True
    if user.lower() in IGNORED_USERS or user.lower().endswith("[bot]"):
        return True
    # Pure mergebot commands ("robodoo r+", "@robodoo delegate=...").
    lines = [l.strip() for l in body.strip().splitlines() if l.strip()]
    return all(re.match(r"^@?(robodoo|fw-bot|mergebot)\b", l, re.I) for l in lines)


def search_prs(gh, user, repo, since):
    q = f"is:pr author:{user} repo:{repo}"
    if since:
        q += f" updated:>={since}"
    return list(gh.paginate("/search/issues", q=q, sort="updated", order="desc"))


def fetch_pr(gh, repo, item):
    num = item["number"]
    pr = gh.get(f"/repos/{repo}/pulls/{num}")
    author = pr["user"]["login"]
    entry = {
        "repo": repo,
        "number": num,
        "url": pr["html_url"],
        "title": pr["title"],
        "base": pr["base"]["ref"],
        "head": pr["head"]["label"],
        "state": "merged" if pr.get("merged_at") else pr["state"],
        "updated_at": pr["updated_at"],
        "inline": [],
        "reviews": [],
        "conversation": [],
    }

    for c in gh.paginate(f"/repos/{repo}/pulls/{num}/comments"):
        login = c["user"]["login"] if c.get("user") else "ghost"
        if c.get("is_copilot_code_review") or (login != author and is_noise(login, c["body"])):
            continue
        entry["inline"].append({
            "id": c["id"],
            "in_reply_to": c.get("in_reply_to_id"),
            "user": login,
            "is_me": login == author,
            "created_at": c["created_at"],
            "path": c["path"],
            "line": c.get("line") or c.get("original_line"),
            "start_line": c.get("start_line") or c.get("original_start_line"),
            "side": c.get("side"),
            "outdated": c.get("line") is None,  # code changed after the comment
            "commit": c.get("original_commit_id"),
            "diff_hunk": c.get("diff_hunk", ""),
            "body": c["body"],
            "url": c["html_url"],
        })

    for r in gh.paginate(f"/repos/{repo}/pulls/{num}/reviews"):
        login = r["user"]["login"] if r.get("user") else "ghost"
        if login == author or is_noise(login, r.get("body")):
            continue
        entry["reviews"].append({
            "user": login, "state": r["state"], "created_at": r.get("submitted_at"),
            "body": r["body"], "url": r["html_url"],
        })

    for c in gh.paginate(f"/repos/{repo}/issues/{num}/comments"):
        login = c["user"]["login"] if c.get("user") else "ghost"
        if is_noise(login, c["body"]):
            continue
        entry["conversation"].append({
            "user": login, "is_me": login == author, "created_at": c["created_at"],
            "body": c["body"], "url": c["html_url"],
        })
    # Keep my own conversation replies only when someone else also commented.
    if not any(not c["is_me"] for c in entry["conversation"]):
        entry["conversation"] = []
    return entry


def has_feedback(entry):
    return (any(not c["is_me"] for c in entry["inline"])
            or entry["reviews"] or entry["conversation"])


# ---------------------------------------------------------------- digest

def quote(text, prefix="> "):
    return "\n".join(prefix + l if l.strip() else prefix.rstrip() for l in text.strip().splitlines())


def tail_hunk(hunk, n=HUNK_TAIL):
    lines = hunk.splitlines()
    if len(lines) > n:
        lines = [f"... ({len(lines) - n} earlier hunk lines omitted)"] + lines[-n:]
    return "\n".join(lines)


def build_threads(entry):
    """Group inline comments into threads rooted at a reviewer comment."""
    by_id = {c["id"]: c for c in entry["inline"]}
    threads = {}
    for c in sorted(entry["inline"], key=lambda c: c["created_at"]):
        root = c
        while root.get("in_reply_to") and root["in_reply_to"] in by_id:
            root = by_id[root["in_reply_to"]]
        threads.setdefault(root["id"], []).append(c)
    # Drop threads that are only my own remarks.
    return [t for t in threads.values() if any(not c["is_me"] for c in t)]


def render_digest(store, user, hunk_lines=HUNK_TAIL):
    prs = sorted(store["prs"].values(), key=lambda e: e["updated_at"], reverse=True)
    by_path = {}
    general = []
    reviewers = {}
    n_threads = 0
    for e in prs:
        ref = f"{e['repo']}#{e['number']}"
        for t in build_threads(e):
            root = t[0]
            by_path.setdefault(root["path"], []).append((e, ref, t))
            n_threads += 1
            for c in t:
                if not c["is_me"]:
                    reviewers[c["user"]] = reviewers.get(c["user"], 0) + 1
        items = [("review " + r["state"].lower(), r) for r in e["reviews"]]
        items += [("conversation", c) for c in e["conversation"]]
        if items:
            general.append((e, ref, sorted(items, key=lambda i: i[1]["created_at"] or "")))
            for _k, c in items:
                if not c.get("is_me"):
                    reviewers[c["user"]] = reviewers.get(c["user"], 0) + 1

    out = [
        f"# Review feedback received by @{user}",
        "",
        f"Synced: {store['synced_at']}  ",
        f"PRs with feedback: {sum(1 for e in prs if has_feedback(e))} / {len(prs)} scanned  ",
        f"Inline threads: {n_threads}  ",
        "Reviewers: " + ", ".join(f"@{u} ({n})" for u, n in
                                  sorted(reviewers.items(), key=lambda x: -x[1])),
        "",
        "Layout: `## path` sections (inline threads, each with the diff hunk the reviewer",
        "commented on, the comment, and replies marked **me**), then `## General PR feedback`",
        "(review summaries and conversation). Lines starting with `@@meta` are grep anchors:",
        "`@@meta repo=... pr=... path=... module=... reviewer=... date=...`.",
        "",
    ]

    for path in sorted(by_path):
        out += [f"## {path}", ""]
        for e, ref, t in sorted(by_path[path], key=lambda x: x[2][0]["created_at"], reverse=True):
            root = t[0]
            module = module_of(path)
            out.append(f"@@meta repo={e['repo']} pr={e['number']} path={path} module={module} "
                       f"reviewer={root['user']} date={root['created_at'][:10]}")
            loc = f"L{root['start_line']}-{root['line']}" if root.get("start_line") else f"L{root['line']}"
            out.append(f"### {ref} `{path}` {loc} — @{root['user']}"
                       f"{' (outdated: code was changed)' if root['outdated'] else ''}")
            out.append(f"PR: [{e['title']}]({e['url']}) · base `{e['base']}` · {e['state']} · "
                       f"[comment]({root['url']})")
            out += ["", "```diff", tail_hunk(root["diff_hunk"], hunk_lines), "```", ""]
            for c in t:
                who = "**me**" if c["is_me"] else f"@{c['user']}"
                out.append(f"{who} ({c['created_at'][:10]}):")
                out.append(quote(c["body"]))
                out.append("")
        out.append("")

    out += ["## General PR feedback", ""]
    for e, ref, items in general:
        out.append(f"@@meta repo={e['repo']} pr={e['number']} path=- module=- "
                   f"reviewer={','.join(sorted({i[1]['user'] for i in items if not i[1].get('is_me')}))} "
                   f"date={(items[0][1]['created_at'] or '')[:10]}")
        out.append(f"### {ref} [{e['title']}]({e['url']}) · base `{e['base']}` · {e['state']}")
        out.append("")
        for kind, c in items:
            who = "**me**" if c.get("is_me") else f"@{c['user']}"
            out.append(f"{who} ({kind}, {(c['created_at'] or '')[:10]}):")
            out.append(quote(c["body"]))
            out.append("")
    return "\n".join(out) + "\n"


def write_digests(out_dir, store):
    """review_comments.md: full hunks, for looking up specific threads.
    review_comments_compact.md: only the commented lines, small enough to distil."""
    (out_dir / "review_comments.md").write_text(render_digest(store, store["user"]))
    (out_dir / "review_comments_compact.md").write_text(render_compact(store))
    print(f"Wrote {out_dir / 'review_comments.md'}\nWrote {out_dir / 'review_comments_compact.md'}")


def render_compact(store):
    """One block per thread: meta line, the commented lines, the discussion."""
    def clip(line, n=160):
        return line if len(line) <= n else line[:n] + " …"

    out = [f"# Compact review feedback for @{store['user']} (synced {store['synced_at']})",
           "# Block = @@meta line, the commented diff lines, then the thread (me = PR author).", ""]
    prs = sorted(store["prs"].values(), key=lambda e: e["updated_at"], reverse=True)
    rows = []
    for e in prs:
        for t in build_threads(e):
            rows.append((t[0]["path"], t[0]["created_at"], e, t))
    for path, _d, e, t in sorted(rows, key=lambda r: (r[0], r[1])):
        root = t[0]
        out.append(f"@@meta repo={e['repo']} pr={e['number']} path={path} module={module_of(path)} "
                   f"line={root['line']} reviewer={root['user']} date={root['created_at'][:10]} "
                   f"base={e['base']} url={root['url']}")
        out += [clip(l) for l in root["diff_hunk"].splitlines()[-COMPACT_HUNK:]]
        for c in t:
            who = "me" if c["is_me"] else "@" + c["user"]
            out.append(f"{who}: " + " ⏎ ".join(l.strip() for l in c["body"].strip().splitlines() if l.strip()))
        out.append("")
    for e in prs:
        items = sorted(e["reviews"] + e["conversation"], key=lambda c: c["created_at"] or "")
        if not items:
            continue
        out.append(f"@@meta repo={e['repo']} pr={e['number']} path=- module=- line=- "
                   f"reviewer={','.join(sorted({c['user'] for c in items if not c.get('is_me')}))} "
                   f"date={(items[0]['created_at'] or '')[:10]} base={e['base']} url={e['url']}")
        out.append(f"PR title: {e['title']}")
        for c in items:
            who = "me" if c.get("is_me") else "@" + c["user"]
            out.append(f"{who}: " + " ⏎ ".join(l.strip() for l in c["body"].strip().splitlines() if l.strip()))
        out.append("")
    return "\n".join(out) + "\n"


def module_of(path):
    parts = path.split("/")
    for i, p in enumerate(parts[:-1]):
        if p == "addons" and i + 1 < len(parts) - 1:
            return parts[i + 1]
    # enterprise / upgrade: module dir is the first component (upgrade: migrations/<module>)
    if parts[0] in ("migrations", "upgrade") and len(parts) > 2:
        return parts[1]
    return parts[0] if len(parts) > 1 else "-"


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", help="GitHub login (default: token owner)")
    ap.add_argument("--repos", nargs="+", default=list(DEFAULT_REPOS))
    ap.add_argument("--since", help="only PRs updated on/after YYYY-MM-DD (overrides incremental)")
    ap.add_argument("--full", action="store_true", help="ignore previous sync and refetch all PRs")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--render-only", action="store_true",
                    help="rebuild review_comments.md from comments.json without calling GitHub")
    args = ap.parse_args()

    if args.render_only:
        store = json.loads((args.out_dir / "comments.json").read_text())
        for e in store["prs"].values():  # re-apply filters (ignored users may have changed)
            e["reviews"] = [r for r in e["reviews"] if not is_noise(r["user"], r["body"])]
            e["conversation"] = [c for c in e["conversation"] if c["is_me"] or not is_noise(c["user"], c["body"])]
            if not any(not c["is_me"] for c in e["conversation"]):
                e["conversation"] = []
        write_digests(args.out_dir, store)
        return

    gh = GitHub(load_token())
    user = args.user or gh.get("/user")["login"]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    store_path = args.out_dir / "comments.json"
    store = {"user": user, "synced_at": None, "prs": {}}
    if store_path.exists() and not args.full:
        store = json.loads(store_path.read_text())
        if store.get("user") != user:
            sys.exit(f"{store_path} belongs to @{store.get('user')}; use --out-dir or --full")

    since = args.since
    if not since and not args.full and store.get("synced_at"):
        last = datetime.fromisoformat(store["synced_at"].replace("Z", "+00:00"))
        since = (last - timedelta(days=1)).strftime("%Y-%m-%d")  # overlap for safety

    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    todo = []
    for repo in args.repos:
        items = search_prs(gh, user, repo, since)
        print(f"{repo}: {len(items)} PR(s) {'updated since ' + since if since else 'total'}")
        todo += [(repo, it) for it in items]

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for entry in pool.map(lambda ri: fetch_pr(gh, *ri), todo):
            store["prs"][f"{entry['repo']}#{entry['number']}"] = entry
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{len(todo)} PRs fetched")

    store["synced_at"] = started
    store["user"] = user
    tmp = store_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=1, ensure_ascii=False))
    tmp.replace(store_path)
    write_digests(args.out_dir, store)

    with_fb = sum(1 for e in store["prs"].values() if has_feedback(e))
    print(f"Fetched {done} PR(s); store has {len(store['prs'])} PR(s), {with_fb} with feedback.")
    print(f"Wrote {store_path}")


if __name__ == "__main__":
    main()
