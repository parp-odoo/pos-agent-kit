# Agent Instructions

This project uses **pos-agent-kit** (Odoo POS agents, skills and scripts) on top
of the **community Odoo skills** shipped in `community/skills/`. Paths below
are relative to this file (the project root). Skills are read in place from
`community/skills/` and `pos-agent-kit/skills/`. The kit does not create or
need `.agents/`, `.claude/` or `.codex/`, but it honors them if they exist
(see *Local agent directories*).

## Settings

Other kit files refer to these values by name.

| Name | Value |
| --- | --- |
| `project_root` | `<project_root_value>` |
| `worktree_root` | `<worktree_root_value>` |
| `odoo_handle` | `<odoo_handle_value>` |
| `github_login` | `<github_login_value>` |

## Where the instructions live

| Path | What | Source |
| --- | --- | --- |
| `community/skills/` | Community Odoo skills | upstream, never edited |
| `pos-agent-kit/skills/` (`odoo-pos`, `niche-review`) | POS kit skills | kit |
| `pos-agent-kit/agents/` | POS, POS test, and worktree agents | kit |
| `pos-agent-kit/overrides/` | Local changes to community skills | kit |
| `pos-agent-kit/scripts/` | Helper scripts used by kit skills | kit |

## Routing

Rules add up: apply every rule that matches the request (for example POS
development plus POS tests), and read only what those rules point to. A task
that is not Odoo work (a generic script, a question about another tool) needs
none of these files.

- **New Odoo worktree setup:** read and follow
  [pos-agent-kit/agents/WORKTREE_AGENT.md](pos-agent-kit/agents/WORKTREE_AGENT.md).
  A setup-only request does not load the POS agents yet; they apply once
  development starts.
- **POS development** (`point_of_sale`, `pos*` modules): read and follow
  [pos-agent-kit/agents/POS_AGENT.md](pos-agent-kit/agents/POS_AGENT.md).
- **Writing, updating or repairing POS tests**, only when the user explicitly
  asks (fixing an existing failing test counts): also read and follow
  [pos-agent-kit/agents/POS_TEST_AGENT.md](pos-agent-kit/agents/POS_TEST_AGENT.md).
- **POS architecture or frontend/backend flow tracing:** use the
  [odoo-pos](pos-agent-kit/skills/odoo-pos/SKILL.md) skill. For an explanation
  it is the only file needed; the POS agents also use it to trace a bug or
  feature before changing code.
- **Commits, branch names, pull requests** (any module): use the community
  `odoo-git` skill with its override (see *Overrides of community skills*).
  A request that only asks for a commit message, branch name or PR text needs
  nothing else, even for a POS module.
- **Niche review** (checking a change against review comments received
  before): use the [niche-review](pos-agent-kit/skills/niche-review/SKILL.md)
  skill. It works offline; never run the fetch script yourself. The user
  refreshes the data with
  `python3 pos-agent-kit/scripts/pr_review_comments/fetch_pr_comments.py`.
- **Other Odoo work:** use the community skills in
  [community/skills/](community/skills/). Pick the matching skill from the
  `description` in each `<skill>/SKILL.md`; ignore that folder's `README.md`,
  which is about installing copies and does not apply here. For reviews:
  `odoo-review` for a diff, commit or PR; `odoo-security` for a security
  audit of existing code.

When a skill is listed here, read its `SKILL.md` from this path yourself; do not
expect the harness to have loaded it. Use other skills offered by the harness
(outside these folders) only when the user asks for them by name.

## Local agent directories

The project root may also have `.agents/`, `.claude/` or `.codex/`, for
example with instructions or skills added by you, a teammate or another
harness. They are not part of the kit and are optional.

- At the start of an Odoo task, check whether any of them exists. If one
  does, look at its top level for instruction files (`AGENTS.md`,
  `CLAUDE.md`, other `*.md` guides) and at `skills/<name>/SKILL.md`, and follow
  the ones that apply to the task, alongside the routing above.
- If a skill there has the same name as a community or kit skill
  (`odoo-git`, `odoo-pos`, ...), use the path routed in this file. Treat the
  local copy as stale. Mention the duplicate once, only when the task would
  have used that skill.
- If a local instruction conflicts with a kit agent or a community skill,
  follow the local instruction (it is specific to this project) and say so.
  It does not override the *Settings* or the kit overrides; see *Precedence*.

## Overrides of community skills

Some community skills have local changes. Never edit the files under
`community/skills/`. When you use one of these skills, read it first, then
apply its override file. The override wins where they conflict.

| Community skill | Override |
| --- | --- |
| `odoo-git` | [pos-agent-kit/overrides/odoo-git.md](pos-agent-kit/overrides/odoo-git.md) |
| `odoo-guidelines` | [pos-agent-kit/overrides/comments.md](pos-agent-kit/overrides/comments.md) |
| `odoo-web-guidelines` | [pos-agent-kit/overrides/comments.md](pos-agent-kit/overrides/comments.md) |

## Precedence

1. The user's explicit instructions in the conversation.
2. The *Settings* above and the kit overrides (`pos-agent-kit/overrides/`):
   these are the user's personal rules, for example no co-author trailer, even
   if a harness or tool asks for one.
3. Instructions in `.agents/`, `.claude/` or `.codex/`, if present (except
   same-name copies of community or kit skills).
4. The kit agents (`pos-agent-kit/agents/`).
5. Kit skills, then community skills.
