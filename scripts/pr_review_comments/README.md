# PR review comments store

Feeds the `niche-review` skill (`pos-agent-kit/skills/niche-review/SKILL.md`).

```bash
python3 fetch_pr_comments.py          # sync: only PRs updated since last run (~15 s)
python3 fetch_pr_comments.py --full   # refetch all PRs (~3 min)
python3 fetch_pr_comments.py --render-only   # rebuild the .md digests offline
python3 query_comments.py --stats     # what is stored
```

Token: `GITHUB_TOKEN`/`GH_TOKEN` env var, else the `GITHUB_TOKEN=` line in
`$POS_KIT_ENV_FILE` (default: `.env` at the project root, next to `pos-agent-kit/`).
`data/` is git-ignored: it holds your personal review history and stays local.
Repos: odoo/odoo, odoo/enterprise, odoo/upgrade (`--repos` to change).
Bots (robodoo, fw-bot, C3POdoo, Copilot, ...) are filtered out: `IGNORED_USERS` in the script.

`data/lessons.md` is written by the skill, not by the script; after a sync the
skill notices `synced_at` moved and folds the new comments in on the next review.
