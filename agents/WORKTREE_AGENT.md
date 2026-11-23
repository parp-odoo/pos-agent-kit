---
name: worktree-agent
description: >-
  Create matching git worktrees for the community, enterprise and x
  repositories under <worktree_root>/<FIX|IMP|RUNBOT|POC>/<task-slug>/, on the
  same task branch (<target>-<topic>-<odoo_handle>) from verified version
  bases, without touching the original checkouts. Use when the user asks for
  a new Odoo worktree or task workspace.
---

# Odoo worktree setup agent

Follow this guide when the user requests a new Odoo worktree. Prepare all three repositories together.

`<project_root>`, `<worktree_root>` and `<odoo_handle>` below are the values from the *Settings* section of the project's `AGENTS.md`.

## Layout and branch selection

Source repositories are `<project_root>/community`, `<project_root>/enterprise`, and `<project_root>/x`. Create worktrees only under `<worktree_root>/<category>/<task-slug>/`, with separate `community/`, `enterprise/`, and `x/` worktrees underneath.

Use one of these exact uppercase category folder names:

| Category | Use |
| --- | --- |
| `IMP` | Features, improvements, and refactoring. |
| `FIX` | Bug fixes and regressions. |
| `RUNBOT` | Runbot failures, investigations, and fixes. |
| `POC` | Proofs of concept and experiments. |

Use an explicitly requested category; otherwise infer it from the task. Prefer `RUNBOT` for Runbot-related work and `POC` for experiments; classify other fixes as `FIX` and improvements as `IMP`. Ask only when the task does not establish a suitable category. Normalize category spelling to the uppercase names above.

This layout is mandatory. Do not create worktrees in `workspace/`, directly under `<worktree_root>/`, or outside these category folders. If a requested destination conflicts with this layout, explain the required location and resolve the conflict before creation. Use a single safe directory component for the task slug; reject absolute paths, path separators, `.` and `..`. Resolve destinations before creation and verify that symlinks or traversal cannot escape `<worktree_root>/<category>/<task-slug>/`.

Use the requested task branch across all three repositories. For a new branch follow the `odoo-git` skill (`<project_root>/community/skills/odoo-git/SKILL.md`) and the [odoo-git overrides](../overrides/odoo-git.md): `<target>-<topic>-<odoo_handle>`. Preserve an explicitly supplied existing branch name.

1. Inspect each repository's status, remotes, exact task refs, and `git worktree list --porcelain`. Validate names with `git check-ref-format --branch`. Resolve all three repositories before making changes; avoid dumping the full branch list.
2. Determine the target from the explicit request, verified PR base, or existing upstream and ancestry. A leading `master-`, `19.0-`, or `saas-19.4-` is evidence to verify, not a substitute for verification. Forward-port names can contain older embedded versions. With no explicit target, use the current community checkout's established target if unambiguous; otherwise ask.
3. Inspect community code using `git show <ref>:odoo/release.py` without executing it. Master may report a future version; do not turn that number into an assumed stable branch. Corroborate master with the upstream or PR base.
4. For each repository independently, reuse the exact local task branch, otherwise track the exact remote task branch, otherwise create the task branch from that repository's matching version base. In x, default to a new task branch from the matching version if no task branch exists. Use a version branch directly only when explicitly requested for a base-only checkout.
5. Confirm the same target version in all three repositories. Never fall back to master when a stable or SaaS base is missing. Report the missing base and ask how to proceed.

## Remotes and freshness

Discover remote names rather than assuming origin. Observed defaults are community `odoo` / development `odoo-dev`, enterprise `ent` / development `ent-dev`, and x `origin`. Confirm each time. Prefer the known task upstream, then the development remote for task branches and official remote for version bases. Ask when conflicting remote task refs lack clear provenance.

Fetch only needed branches from the selected remotes. Prefer freshly fetched remote version bases; never move local version branches backwards or base new work on unrelated local commits. If fetching fails, report it and explicitly disclose any use of cached refs.

## Create worktrees

A request for new worktree setup authorizes local worktree and missing task branch creation, but not pushing. Use Git worktrees, not copies or symlinks. Quote every path and ref. Execute the applicable form separately for community, enterprise, and x:

```bash
# Existing local task branch
git -C "$source_repo" worktree add "$destination" "$task_branch"

# Remote task branch only
git -C "$source_repo" worktree add --track -b "$task_branch" "$destination" "$remote_task_ref"

# Missing task branch: use the repository's matching version base
git -C "$source_repo" worktree add -b "$task_branch" "$destination" "$version_base_ref"
```

Preserve the original checkouts and their staged, unstaged, and untracked files. Never switch them during setup. Do not stash, reset, clean, force checkout, or force-remove automatically.

If a branch is already checked out elsewhere, report its path. Reuse only if it satisfies the mandatory category/task layout under `<worktree_root>`; otherwise report the conflict and ask whether to create a distinct branch in the required location. Do not reuse an out-of-layout worktree for this setup or move it automatically. Never bypass Git restrictions with `--force` or silently use detached HEAD. Verify existing destinations before reuse and never overwrite unrelated directories. Do not prune registrations or delete branches during setup.

If setup partially fails, preserve the successful worktrees and report what remains. Resume from that state on retry.

## Verify and hand off

Create a workspace-root `AGENTS.md` pointing to `<project_root>/AGENTS.md` if none exists; preserve existing instructions. Read the source instructions and any applicable POS guides before development. Do not copy source changes into the new repositories.

Verify that each worktree is located at `<worktree_root>/<category>/<task-slug>/<repository>` with category `IMP`, `FIX`, `RUNBOT`, or `POC`. Verify status, branch, HEAD, and base ancestry in each worktree. Check community release metadata and enterprise/x version provenance. Ensure any supplied Odoo invocation uses the new community, enterprise, and x paths together. Do not create databases, install dependencies, or alter server configuration unless the task requires it.

Report the workspace path and a three-row table with repository, branch, base/upstream, and whether the branch was reused or created.

## Usage examples

- Create a new FIX worktree for `19.0-pos-portal-fix-<odoo_handle>`.
- Start an IMP master worktree for POS payment cleanup.
- Set up `saas-19.4-pos-receipt-fix-<odoo_handle>` in community, enterprise, and x under FIX.
- Create a RUNBOT worktree to investigate a failing POS tour.
- Create a POC worktree for a payment experiment.

Creating or editing this guide alone does not authorize creating task worktrees.
