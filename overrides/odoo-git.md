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
- Wrap technical names in backticks in the body: models, fields, methods,
  functions, classes, components, files, XML ids, settings
  (`pos.order`, `amount_total`, `_compute_price()`, `ProductScreen`).
  The header stays as it is, with the module name in plain text.

Replaces the bug-fix bullet in *Body*:

- For a bug fix, give the steps that reproduce the bug: what to do, what
  happens, what should happen. Lead with the reported case and explain the
  resulting behavior. A fix message without the reported steps is not finished.
  (Do not refer to the test to show which cases the fix covers.)

Addition to *Body*, for a bug or error that an earlier commit introduced:

- Name the commit that introduced it in the body. Give its hash only, never
  its title after it: `Since commit 1a2b3c4d5e6f, ...`, not
  `Since commit 1a2b3c4d5e6f ([FIX] point_of_sale: ...), ...`.
- Say in a single sentence why that commit causes the break. Do not go deeper
  into its history or its changes.
- After writing the message, give the user a GitHub link to each commit it
  names, in your reply and not in the commit message:
  `https://github.com/<owner>/<repo>/commit/<full hash>`, with the owner and
  repository of the Odoo repository the commit lives in (for example
  `odoo/odoo` or `odoo/enterprise`).

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

## Pull requests

Addition to *Branches and pull requests*:

- Always open a pull request as a draft (`gh pr create --draft`) when asked to
  create one. Open it ready for review only when the user explicitly asks for
  that (an open, non-draft or ready-for-review PR). Do not mark a draft ready
  for review (`gh pr ready`) unless the user asks.
- Links in the PR description, added without being asked:
  - For each commit the commit message names as the cause of the bug, link
    the hash in the description:
    `[1a2b3c4d5e6f](https://github.com/<owner>/<repo>/commit/<full hash>)`.
  - For a `runbot-<id>` trailer, put its link in the footer of the
    description: `runbot-<id>: https://runbot.odoo.com/odoo/error/<id>`.
  - Leave `task-` and `opw-` references as plain text, without a link.
  The commit message itself keeps the plain hash and the plain `runbot-<id>`
  trailer.
