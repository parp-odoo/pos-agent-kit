# Comments and docstrings overrides

Local rules on top of the community
[odoo-guidelines](../../community/skills/odoo-guidelines/SKILL.md) and
[odoo-web-guidelines](../../community/skills/odoo-web-guidelines/SKILL.md)
skills, for any code you write or change (Python, JavaScript, XML, SCSS,
tests). The community rule on
[plain ASCII punctuation](../../community/skills/odoo-guidelines/guidelines/comments.md)
still applies to the comments you do write.

## Do not add unnecessary comments or docstrings

- Do not add a comment that restates what the code does. Good names and small
  functions explain the what; the diff explains the change.
- Write a comment only for what the code cannot say: a non-obvious why, a
  workaround and the case it handles, a constraint from another module or an
  external system. Keep it to one or two lines.
- Do not add docstrings to methods, functions, classes or components by
  default. Add one only for a public API or extension point that other modules
  are expected to override or call, and only when its contract is not obvious
  from the signature.
- No JSDoc type blocks or `@param`/`@returns` annotations that repeat the code.
- No comments about the task or the change itself (`# fix for ...`,
  `// added for task-123`, `# new: ...`, `# changed from ...`); that belongs in
  the commit message.
- No commented-out code, no section banners, no `TODO` unless the user asks for
  one.
- Do not add or reword comments and docstrings in code you are not otherwise
  changing.
- Keep existing useful comments; update one only when your change makes it
  wrong.
