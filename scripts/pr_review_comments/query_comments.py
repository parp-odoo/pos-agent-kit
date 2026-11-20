#!/usr/bin/env python3
"""Query the stored review feedback (data/comments.json) offline.

Used by the niche-review skill. Never calls GitHub.

  query_comments.py --stats
  query_comments.py --files addons/point_of_sale/models/pos_order.py ...   # threads on these files,
                                            # same file name elsewhere, or same directory
  query_comments.py --modules point_of_sale pos_restaurant                 # threads in these modules
  query_comments.py --files ... --full-hunk                                # whole diff hunk, not the tail
  query_comments.py --since 2026-10-01                                     # threads created on/after
  query_comments.py --chunk 2/4                                            # 2nd quarter of everything
  query_comments.py --general                                              # also review summaries / conversation

Output: one block per thread, `@@meta ...` line, the diff hunk lines the
reviewer commented on, then each message (`me:` = the PR author).
"""

import argparse
import json
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_pr_comments import COMPACT_HUNK, DEFAULT_OUT, build_threads, module_of  # noqa: E402


def one_line(body):
    return " ⏎ ".join(l.strip() for l in body.strip().splitlines() if l.strip())


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=DEFAULT_OUT / "comments.json")
    ap.add_argument("--files", nargs="*", default=[], help="repo-relative paths from the diff")
    ap.add_argument("--modules", nargs="*", default=[])
    ap.add_argument("--since", help="YYYY-MM-DD, threads started on/after")
    ap.add_argument("--reviewer", nargs="*", default=[])
    ap.add_argument("--full-hunk", action="store_true")
    ap.add_argument("--hunk-lines", type=int, default=COMPACT_HUNK)
    ap.add_argument("--general", action="store_true", help="include non-inline PR feedback")
    ap.add_argument("--chunk", help="i/N: only the i-th of N equal slices (1-based)")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    store = json.loads(args.data.read_text())
    prs = sorted(store["prs"].values(), key=lambda e: e["updated_at"], reverse=True)

    blocks = []  # (path, date, text)
    for e in prs:
        for t in build_threads(e):
            root = t[0]
            path, date = root["path"], root["created_at"][:10]
            if args.files:
                if path in args.files:
                    match = "exact-file"
                elif Path(path).name in {Path(f).name for f in args.files}:
                    match = "same-name"
                elif str(Path(path).parent) in {str(Path(f).parent) for f in args.files}:
                    match = "same-dir"
                else:
                    continue
            else:
                match = ""
            if args.modules and module_of(path) not in args.modules:
                continue
            if args.since and date < args.since:
                continue
            if args.reviewer and root["user"] not in args.reviewer:
                continue
            hunk = root["diff_hunk"].splitlines()
            if not args.full_hunk:
                hunk = hunk[-args.hunk_lines:]
            lines = [f"@@meta repo={e['repo']} pr={e['number']} path={path} module={module_of(path)} "
                     f"line={root['line']} reviewer={root['user']} date={date} base={e['base']} "
                     f"{'match=' + match + ' ' if match else ''}"
                     f"{'outdated ' if root['outdated'] else ''}url={root['url']}"]
            lines += hunk
            lines += [f"{'me' if c['is_me'] else '@' + c['user']}: {one_line(c['body'])}" for c in t]
            # exact-file matches first, then by path/date
            blocks.append(({"exact-file": 0, "same-name": 1}.get(match, 2), path, date, "\n".join(lines)))
        if args.general and not args.files and not args.modules and not args.reviewer:
            items = sorted(e["reviews"] + e["conversation"], key=lambda c: c["created_at"] or "")
            date = (items[0]["created_at"] or "")[:10] if items else ""
            if items and not (args.since and date < args.since):
                lines = [f"@@meta repo={e['repo']} pr={e['number']} path=- date={date} base={e['base']} url={e['url']}",
                         f"PR title: {e['title']}"]
                lines += [f"{'me' if c.get('is_me') else '@' + c['user']}: {one_line(c['body'])}" for c in items]
                blocks.append((3, "~", date, "\n".join(lines)))

    blocks.sort(key=lambda b: (b[0], b[1], b[2]))
    if args.chunk:
        i, n = map(int, args.chunk.split("/"))
        size = -(-len(blocks) // n)
        blocks = blocks[(i - 1) * size:i * size]

    if args.stats:
        mods = {}
        for _o, path, _d, _t in blocks:
            mods[module_of(path)] = mods.get(module_of(path), 0) + 1
        print(f"user=@{store['user']} synced_at={store['synced_at']} threads={len(blocks)}")
        for m, n in sorted(mods.items(), key=lambda x: -x[1]):
            print(f"  {n:5d}  {m}")
        return
    print(f"# @{store['user']} review feedback, synced {store['synced_at']}, {len(blocks)} block(s)\n")
    print("\n\n".join(b[3] for b in blocks))


if __name__ == "__main__":
    main()
