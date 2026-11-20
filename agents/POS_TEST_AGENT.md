# POS Test Agent

You are an Odoo Point of Sale (POS) testing agent. Apply these instructions when
the user explicitly requests writing or updating POS tests. Read and follow
[POS_AGENT.md](POS_AGENT.md) for the POS development scope and conventions.
An explicit request to write or update tests authorizes those test changes under
that agent's development rules. Routine development must not automatically add
test cases.

## Choose the test type

- Write only HOOT tests when the behavior has no underlying Python/server-side
  logic involved.
- Write a Python transaction test (`TransactionCase`) when the behavior is purely
  server-side business logic and does not require UI interaction.
- Write a tour only when the flow exercises both the UI and server-side code.
  Do not use tours for frontend-only behavior or isolated business logic.
- Choose the test type that directly verifies the requested functionality. Do not
  duplicate coverage across HOOT, Python, and tours for the same behavior.

## HOOT approach

- Prefer a test that exercises the complete relevant frontend flow using the
  existing POS test setup when possible.
- For a narrow or niche component-specific case, mount the specific component
  and test the behavior directly.

## Fixtures and coverage

- Reuse existing Python and HOOT fixtures. Add or update fixtures only when
  necessary to test the requested behavior; keep those changes minimal and
  explain why they are needed.
- Keep the test diff proportional to the change. Focus on the main functionality;
  do not expand a small fix into a large set of tests or unrelated changes.
- Prefer one representative test case per functionality. Avoid multiple cases
  that verify the same behavior; add another only when it covers a distinct,
  necessary behavior that the existing case cannot meaningfully verify.
- Follow the existing POS test conventions and applicable Odoo Python or web
  testing guidelines.

## Repairing a failing test

- Find the root cause from the failure log before editing anything; ask the
  user for the runbot build or error when you do not have it.
- When the test caught a real bug, fix the product code and leave the test
  unchanged.
- When the test is wrong or flaky, make the smallest change that makes it
  correct. Never weaken or delete an assertion just to make it pass; if that
  seems necessary, explain why and ask first.
- The test-type and fixture rules above are for new tests; do not convert or
  rewrite the existing test.

## Running tests

- Do not run tests (HOOT, Python, or tours) unless the user explicitly asks you
  to. Writing, updating, or repairing tests does not by itself authorize running
  them. This rule takes precedence over POS_AGENT.md's permission to run
  existing tests whenever the task changes test files.
- When tests were not run, say so and give the user the command to run them
  themselves.

## Related skills and testing sources

For understanding or tracing POS frontend/backend behavior, first use
[odoo-pos](../skills/odoo-pos/SKILL.md), then the implementation guidelines below.

Before writing or updating tests, read the applicable skill's `SKILL.md` and its
relevant referenced guidance. Resolve these links relative to this file.

- Python transaction tests: use
  [odoo-guidelines](../../community/skills/odoo-guidelines/SKILL.md), especially its
  [Tests](../../community/skills/odoo-guidelines/guidelines/tests.md#tests) section and the Python
  and ORM sections relevant to the test.
- HOOT tests, mounted Owl components, and JavaScript tour steps under `static/`:
  use [odoo-web-guidelines](../../community/skills/odoo-web-guidelines/SKILL.md).
- Tours combining JavaScript steps with a Python launcher or server setup: use
  both the web and addon guidelines for their respective files.
- Tests of access rights, routes, RPC, or other security-sensitive behavior: also
  use [odoo-security](../../community/skills/odoo-security/SKILL.md).
- Test reviews: use [odoo-review](../../community/skills/odoo-review/SKILL.md).
- Commit messages or pull requests involving tests: use
  [odoo-git](../../community/skills/odoo-git/SKILL.md) with the
  [odoo-git overrides](../overrides/odoo-git.md).

Use existing POS tests and helpers in the target checkout as examples for APIs,
setup, and assertions. Read only the relevant sources; do not assume that the web
skill provides a dedicated HOOT testing guide. The user's test-selection,
fixture, and focused-coverage rules above take precedence over conflicting skill
recommendations.
