# pos-agent-kit

Agent instructions, skills and scripts for Odoo POS development, used on top of
the community Odoo skills in `community/skills/` (read in place, never copied).

## Contents

| Path | What |
| --- | --- |
| `AGENTS.template.md` | Project `AGENTS.md`: settings, routing, overrides, precedence |
| `install.sh` | Writes `<project>/AGENTS.md` from the template |
| `agents/` | `POS_AGENT`, `POS_TEST_AGENT`, `WORKTREE_AGENT` |
| `skills/odoo-pos/` | POS frontend/backend flow tracing |
| `skills/niche-review/` | Review against comments you received before |
| `overrides/` | Your changes to community skills (`odoo-git.md`, `comments.md`) |
| `scripts/pr_review_comments/` | Fetch/query PR review comments for niche-review |

## Setup

1. Clone the kit into the Odoo project root, next to `community/`:

   ```bash
   git clone <kit-repo-url> pos-agent-kit
   ```

2. Write the project `AGENTS.md` with your settings:

   ```bash
   pos-agent-kit/install.sh --handle <odoo-handle> --github <github-login> \
       --worktree-root ~/odoo-git-worktrees
   ```

   If an `AGENTS.md` already exists, it is left alone; merge
   `AGENTS.template.md` into it by hand.

3. Restart the agent session.

4. Optional, for niche-review: put `GITHUB_TOKEN=...` in `~/odoo/.env`, then
   fetch your review comments:

   ```bash
   python3 pos-agent-kit/scripts/pr_review_comments/fetch_pr_comments.py
   ```

## Notes

- Do not edit `community/skills/`; put changes in `overrides/` and
  list them in `AGENTS.template.md`.
- The template is not named `AGENTS.md` so harnesses don't load its
  placeholders as instructions.
