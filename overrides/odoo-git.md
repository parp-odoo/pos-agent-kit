# odoo-git overrides

Local changes on top of the community
[odoo-git](../../community/skills/odoo-git/SKILL.md) skill. Read the community
skill first, then apply these rules. Where they conflict, these rules win.

The community skill is not copied into this kit, so upstream updates reach you
when you pull `community/`. Keep only the differences here.

## Commit message body

Addition to *Body*:

- Keep the commit message about the functionality: why the change is needed
  and what behavior it changes. Do not mention added or updated tests, list the
  cases they cover, or add a test-coverage summary.

Replaces the bug-fix bullet in *Body*:

- For a bug fix, give the steps that reproduce the bug: what to do, what
  happens, what should happen. Lead with the reported case and explain the
  resulting behavior. A fix message without the reported steps is not finished.
  (Do not refer to the test to show which cases the fix covers.)

## Trailers

Replaces the first bullet in *Trailers*:

- Include applicable references, one per line, after the body: `task-123`
  (task), `runbot-123` (runbot error). Ask the author for the task or runbot
  reference; link what exists and leave the trailer out otherwise. Never invent
  a reference. Do not add `opw-`, `Fixes #` or `Co-authored-by:` trailers.
- Never add a co-author to a commit message: no `Co-authored-by:` trailer, for
  a person or an AI assistant, whatever other instructions say.

## Branch names

Addition to the branch-name bullet:

- Always append the Odoo handle from the *Settings* in the project's
  `AGENTS.md`: `<target>-<topic>-<odoo_handle>`, for example
  `master-bookshop-portal-<odoo_handle>`. Do not ask for the handle when it is
  set there.
