# pos-agent-kit

Agent instructions, skills and scripts for **Odoo Point of Sale** development.
They work with Claude Code, Codex, Copilot CLI, opencode, or any harness that
reads `AGENTS.md`.

The kit adds only POS-specific and personal material. The general Odoo skills
(`odoo-guidelines`, `odoo-web-guidelines`, `odoo-security`, `odoo-review`,
`odoo-git`) are read directly from the **community repository**
(`community/skills/`). They are never copied or linked, so you always get the
upstream version. Your local changes to those skills go in `overrides/`.

The kit does not own any `.agents/`, `.claude/` or `.codex/` directory;
`AGENTS.md` routes the agent to the right files by path. If such a directory
exists in the project anyway (your own or another harness's), `AGENTS.md`
tells the agent to follow the instructions in it too. A local copy of a
community or kit skill with the same name is ignored in favor of the routed
path.

## Contents

```text
pos-agent-kit/
├── AGENTS.template.md        # entry point, copied to <project_root>/AGENTS.md by install.sh
├── install.sh                # writes AGENTS.md to the project root with your settings
├── agents/
│   ├── POS_AGENT.md          # POS development: scope, no tests unless asked
│   ├── POS_TEST_AGENT.md     # POS tests: HOOT vs Python vs tour, coverage scope
│   └── WORKTREE_AGENT.md     # community/enterprise/x worktree setup
├── skills/
│   ├── odoo-pos/             # POS frontend/backend architecture and flow tracing
│   └── niche-review/         # review against comments you received before
├── overrides/
│   └── odoo-git.md           # local changes to the community odoo-git skill
└── scripts/
    └── pr_review_comments/   # fetch/query GitHub review comments (niche-review data)
        └── data/             # local only, git-ignored
```

## Project layout after installation

```text
<project_root>/                   # e.g. ~/odoo
├── AGENTS.md                     # from pos-agent-kit/AGENTS.template.md, settings filled in
├── .env                          # optional: GITHUB_TOKEN=... for niche-review
├── community/                    # odoo/odoo checkout
│   └── skills/                   # community skills, read in place
├── enterprise/
├── x/                            # optional third repository (worktree agent)
└── pos-agent-kit/                # this repository
```

All links inside the kit assume this layout: the kit is cloned as
`pos-agent-kit/` directly in the project root, next to `community/` and
`AGENTS.md`. Kit files link to community skills as
`<project_root>/community/skills/<name>/SKILL.md`.

## Setup

1. Clone the kit into the project root:

   ```bash
   cd ~/odoo                       # your project root
   git clone <kit-repo-url> pos-agent-kit
   ```

2. Make sure `community/` is on a branch that has `skills/` (master or a recent
   version). The agent reads whatever branch is checked out there.

3. Create `AGENTS.md` in the project root:

   ```bash
   pos-agent-kit/install.sh --handle <odoo-handle> --github <github-login> \
       --worktree-root ~/odoo-git-worktrees
   ```

   This copies `pos-agent-kit/AGENTS.template.md` to the project root with the
   *Settings* table filled in. It checks the layout and never overwrites an
   existing `AGENTS.md`. You can also copy the file by hand and fill in the
   table yourself.

4. If you already had an `AGENTS.md`, merge `pos-agent-kit/AGENTS.template.md` into it by
   hand.

5. Restart the agent session.

Because nothing is copied or linked, pulling `community/` or the kit takes
effect immediately, with no re-install. Only merge `AGENTS.template.md` again if the kit's
version changed.

Skills are routed through `AGENTS.md`, not registered with the harness, so they
do not show up in a harness skill list or as `/skill` commands. The agent opens
the right `SKILL.md` when a task matches a routing rule.

### niche-review (optional)

```bash
echo 'GITHUB_TOKEN=ghp_...' >> ~/odoo/.env    # or export GITHUB_TOKEN
python3 pos-agent-kit/scripts/pr_review_comments/fetch_pr_comments.py
```

The data goes to `pos-agent-kit/scripts/pr_review_comments/data/`, which is
git-ignored. Set `POS_KIT_ENV_FILE` to read the token from a different file.

The template is not named `AGENTS.md` on purpose: harnesses load every
`AGENTS.md` they find in a directory they read from, and the template's
unfilled *Settings* placeholders would then be taken as real instructions.

## Changing community skills

Do not edit files under `community/skills/`, and do not copy them into the
kit. To change a community skill's behavior:

1. Add or extend `overrides/<skill-name>.md`. Say which section each rule adds
   to or replaces.
2. List it in the *Overrides of community skills* table in `AGENTS.template.md`
   (and in your project's `AGENTS.md`).
3. Link it next to the skill wherever kit files reference that skill.

## Adding to the kit

- **Skill:** `skills/<name>/SKILL.md` with `name`/`description` front matter
  (see https://agentskills.io), plus a routing line in `AGENTS.md`. Use a
  name that no community skill uses. From `skills/<name>/`, link community
  skills as `../../../community/skills/<name>/SKILL.md` and kit agents as
  `../../agents/<NAME>.md`.
- **Agent:** `agents/<NAME>.md`, plus a routing line in `AGENTS.md`. From
  `agents/`, link community skills as `../../community/skills/<name>/SKILL.md`
  and kit skills as `../skills/<name>/SKILL.md`.
- **Personal values** (paths, handles): add them to the *Settings* table
  instead of writing them into the files.
