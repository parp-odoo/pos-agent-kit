---
name: niche-review
description: >-
  Review a diff, branch, commit or PR against the review comments the user
  has already received on past PRs, so the same remarks do not come back.
  Reads the locally stored feedback (with the diff hunk each comment was made
  on) and a distilled lessons checklist. Use when asked for a niche review,
  a "my-reviewers" review, a pre-push/pre-PR self check, or "review so I don't
  get the same comments again".
---

# Niche review: catch the comments I always get

The general Odoo rules live in `community/skills/odoo-review/SKILL.md` (from the
project root). This skill is
narrower: it checks a change against what *my own reviewers* have actually
asked me to fix before, and nothing else unless the user also asks for a
full review.

## Data (never fetch from GitHub here)

All under `pos-agent-kit/scripts/pr_review_comments/` (from the project root,
the directory holding `AGENTS.md`). `data/` is local and git-ignored:

| File | What |
| --- | --- |
| `data/comments.json` | raw store, `synced_at`, every inline thread with `diff_hunk`, review summaries, conversation |
| `data/review_comments_compact.md` | every thread, commented lines only; source for distillation |
| `data/review_comments.md` | same with up to 40 hunk lines; grep `@@meta ... pr=<n>` to read one thread with context |
| `data/lessons.md` | distilled checklist, built and kept current by this skill (see step 1) |
| `query_comments.py` | offline query tool: `--files`, `--modules`, `--since`, `--reviewer`, `--full-hunk`, `--general`, `--chunk i/N`, `--stats` |
| `fetch_pr_comments.py` | the sync script; the **user** runs it, do not run it unless asked |

In the query output `me:` is the PR author (the user) and `@login:` a
reviewer; `outdated` means the code was changed after the comment, which
usually means the remark was accepted and fixed.

If `comments.json` is missing, stop and tell the user to run
`python3 pos-agent-kit/scripts/pr_review_comments/fetch_pr_comments.py`.
If `synced_at` is older than 30 days, say so in the report and carry on.

## Process

### 1. Make sure `data/lessons.md` is current

`lessons.md` starts with a line `source_synced_at: <timestamp>`. Compare it
with `synced_at` from `query_comments.py --stats`.

- **Up to date:** read it and go to step 2.
- **Missing:** build it. Run `query_comments.py --general --stats` for the
  thread count, then distil in parallel: one subagent per
  `query_comments.py --general --chunk i/4` slice (≈40k tokens each). Give
  each the distillation brief below and the exact command for its slice.
  Merge their outputs yourself: deduplicate, merge same-rule entries and sum
  their counts, keep at most 5 citation URLs per rule.
- **Stale:** distil only `query_comments.py --general --since <source_synced_at date minus 1 day>`
  (yourself if small, a subagent if large) and merge into the existing rules:
  bump counts, add citations, add new rules. Never drop existing rules.

Then write `lessons.md` with the new `source_synced_at`.

**Distillation brief** (for each subagent): "Read every block printed by
`<command>`. Each block is one review thread on a PR by the author (`me`):
the diff lines a reviewer commented on, then the discussion. Extract
reusable rules: the general practice the reviewer asked for, not the
one-off fix. Skip pure questions answered with no change, praise, rebases,
targeting/branch notices, and thanks. For each rule return: a one-line
imperative rule; scope (python / js-owl / xml-views / tests / upgrade /
commit-message / pr-process / any) and the modules it was seen in; a tiny
before→after example taken from the hunk when one exists; the reviewers who
said it; how many threads; up to 3 comment URLs. Group duplicates within
your slice. Return markdown only."

`lessons.md` layout:

```markdown
source_synced_at: 2026-11-18T13:34:25Z

## <scope>
- **<rule>** — ×<count>, @reviewer… — modules: … — e.g. `before` → `after` — [1](url) [2](url)
```

Order rules within a scope by count; rules seen ≥3 times or from several
reviewers go first, marked **(recurring)**.

### 2. Scope the change

Follow step 1 (Scope) of `community/skills/odoo-review/SKILL.md`: work in the checkout of
the revision under review, pin head and base, take the diff from git (for a
PR: its head and base branch; for local work: `git diff <base>...HEAD` plus
uncommitted changes). Do it for every repository the change touches
(community, enterprise, upgrade, sibling branches of the same name). Read
the commit messages too: some lessons are about them. List the changed
files and their modules.

### 3. Pull the past threads that touch the same code

```bash
cd pos-agent-kit/scripts/pr_review_comments   # from the project root
python3 query_comments.py --files <every changed path, repo-relative>
python3 query_comments.py --modules <touched modules>   # only if the first gives < ~15 threads
```

`match=exact-file` and `same-name` threads matter most. For each relevant
thread, compare the hunk the reviewer commented on with the matching part
of the current diff: same construct, same mistake? When the tail is not
enough, re-run with `--full-hunk` on that file or read the block by `pr=` in
`data/review_comments.md`. If the old thread is `outdated`, the fix the
reviewer wanted is in that PR; open the comment URL with `gh`/the API only
if the user asks.

### 4. Review

Go through the diff hunk by hunk, applying:

1. every lessons.md rule whose scope matches the file type, recurring ones
   first;
2. every specific thread from step 3 (reviewer preferences in this very
   file or directory: naming, where code lives, patterns they rejected).

Report only what this diff actually does. A finding needs a line in the
diff and a past comment it repeats; anything else belongs in a regular
review, so leave it out (or list it separately if the user also asked for a
full review).

### 5. Report

Most likely to be flagged again first:

```
<path>:<line> — <what is wrong, one sentence>
  Past comment: @reviewer on <repo>#<pr> "<short quote>" <url>  (×N similar)
  Fix: <concrete change, or a suggestion block>
```

Then a short section "Recurring rules checked, nothing found" listing the
recurring rules that applied to this diff and passed, so the user knows
they were covered. Do not edit code unless asked; when asked to fix, apply
the fixes and re-run step 4 on the changed hunks.
