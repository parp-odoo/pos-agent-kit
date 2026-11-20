---
name: odoo-pos
description: >-
  Explain and trace Odoo Point of Sale frontend and backend behavior together.
  Use for POS architecture questions, following a feature from UI interaction
  through frontend models and synchronization to Python processing, or locating
  the right POS extension point before development or testing.
---

# Odoo POS frontend and backend

Explain POS as one connected flow: what the cashier does, how browser state
changes, what crosses the server boundary, what Python persists or computes,
and how the result returns to the UI. Use the target checkout as the source of
truth; the map below reflects recent master development code and is a
starting point, not a guarantee for other branches. Check the target version
(`odoo/release.py` and the branch's base) before relying on it.

## Find the implementation

The main addon is `community/addons/point_of_sale`. Community extensions live in
`community/addons/pos*`; Enterprise extensions live in `enterprise/pos*`.
Resolve these paths against the workspace, locating equivalent addons paths if
the checkout differs. Check the target version and each relevant module's
manifest before describing its behavior. Search definitions and callers with
`rg`; confirm that named methods and paths exist in that checkout.

Within `point_of_sale`, start with the files matching the question:

| Concern | Sources relative to the addon |
| --- | --- |
| Assets and dependencies | `__manifest__.py` |
| POS page and session bootstrap | `controllers/main.py`, `views/pos_assets_index.xml` |
| Browser startup and root UI | `static/src/app/main.js`, `static/src/app/pos_app.js` |
| Frontend orchestration | `static/src/app/services/pos_store.js` |
| Screens and UI interactions | `static/src/app/screens/`, `static/src/app/components/` |
| Data loading, RPC, cache, connectivity | `static/src/app/plugins/pos_data_plugin.js` |
| Frontend records and relations | `static/src/app/models/`, especially `related_models/` and `data_service_options.js` |
| Payment validation | `static/src/app/screens/payment_screen/payment_screen.js`, `static/src/app/utils/order_payment_validation.js` |
| Backend configuration and sessions | `models/pos_config.py`, `models/pos_session.py` |
| Loading fields, domains, relations | `models/pos_load_mixin.py` and each loaded model's overrides |
| Orders, lines, payments | `models/pos_order.py`, `models/pos_order_line.py`, `models/pos_payment.py`, `models/pos_payment_method.py` |
| Receipts | `receipt/`, frontend printer utilities and plugins |

Do not assume an older `PosDB`, `create_from_ui`, or standalone data-service
architecture applies. This checkout uses `PosDataPlugin`, related frontend
records, and `sync_from_ui`; follow the implementation found on the target branch.

## The connected lifecycle

1. **Open a POS.** The POS controller resolves the configuration and session,
   establishes the company context, and renders the page with bootstrap values.
   The production assets start `main.js`, which mounts the root `Chrome` UI.
   `PosStore` orchestrates POS behavior with services and plugins.
2. **Load data.** `PosDataPlugin` loads cached data and calls
   `pos.session.load_data`. The session's `_load_pos_data_models` chooses models;
   `pos.load.mixin` and model overrides supply fields, domains, dependencies,
   relations, and readable records. The response can include metadata and cache
   removals, not just a flat list of records. The plugin initializes related
   models and loads connected records for the frontend.
3. **Work in the UI.** Owl screens and components use the POS store and frontend
   records such as `PosOrder`, order lines, and payments. UI-only state belongs
   separately from persisted business data. Editing a browser record is not by
   itself proof that the server has saved it. Trace the action to its pending
   changes and synchronization trigger.
4. **Validate and synchronize.** Payment validation goes through `PosStore` and
   `OrderPaymentValidation`. `syncAllOrders` serializes pending orders with
   `serializeForORM` and calls `pos.order.sync_from_ui` through the data plugin.
   Draft orders may also synchronize before payment. Read the actual payload,
   context, relation commands, and UUID handling when explaining a feature.
5. **Process on the server.** `sync_from_ui` finds existing orders and creates,
   updates, or handles them according to their state. `_process_order` processes
   order values, lines, and payments; `_process_saved_order` handles subsequent
   business processing, including paid-state logic and invoicing where applicable.
   Accounting also involves session processing. Inventory behavior is extended
   by `pos_stock` in this checkout; inspect its hooks and configuration before
   claiming when pickings or stock moves are created.
6. **Return and recover.** The server returns POS records through `read_pos_data`;
   the frontend resolves missing relations and merges connected data. Follow the
   caller to the resulting screen or receipt. IndexedDB caches data and local
   changes, while connectivity and synchronization logic handle retries. Trace
   the relevant error branch: browser validation, local persistence, and server
   confirmation are separate events. Do not promise every action works offline.

For a particular feature, follow this chain in both directions:

```text
UI action -> screen/store -> frontend records -> serialization/RPC
          -> Python model and extension hooks -> saved state/response
          -> frontend record merge -> visible result
```

Some interactions remain entirely in the browser, and some backend operations
have no POS screen. Identify the actual boundary rather than forcing every
feature through every step.

## Trace a feature across modules

- Follow the relevant POS addon in both repositories. Restaurant, loyalty,
  sales, inventory, self-order, payment terminals, and preparation displays can
  extend different parts of the flow. Self-order has its own entry points;
  do not assume the cashier UI's route and store are its entry points.
- For a field change, trace its Python declaration, POS loading, frontend use,
  serialization, server handling, and response where applicable. Distinguish
  defaults, UI state, computed values, and stored fields.
- For amounts, discounts, taxes, refunds, or payments, inspect frontend
  calculations and the backend rules or recomputation. Check currency rounding,
  order state, session/company context, and relevant overrides.
- For sync issues, distinguish local IDs, UUIDs, and server IDs; check pending
  changes, cache restoration, retries, and duplicate handling at both ends.
  Bus notifications are a separate update path from an RPC response.
- Prefer existing POS extension points. Follow the user's scope rule in
  [POS_AGENT.md](../../agents/POS_AGENT.md) before changing shared or base code.

## Explain the result

Lead with the user-visible behavior, then connect the frontend action to the
server operation and the returned UI result. Name only the methods needed to
understand that flow and link the source files you actually inspected. State
which addon owns each extension and which details depend on configuration or
version. If a link in the flow is unverified, say so instead of filling it from
memory. Keep a requested summary short; expand only the relevant flow.

## Writing "PoS"

When you add text that names the Point of Sale, write it as `PoS` (lowercase
`o`), not `POS` or `Pos`:

- New code comments and docstrings: `# keep the PoS session open`.
- New user-facing strings, labels and messages:
  `_("Open the PoS to continue")`.

Leave alone:

- Identifiers and technical names: `pos.order`, `pos_config`, `PosStore`,
  `point_of_sale`, XML ids, CSS classes.
- Existing strings, unless the task changes them anyway. Rewording a
  translatable string breaks its translations, and a cosmetic rename does
  not belong in a stable branch.
- Commit messages: follow `odoo-git` (module names such as `point_of_sale`).

## Related skills

This skill maps behavior; use the matching house rules when developing or
reviewing it:

- [odoo-guidelines](../../../community/skills/odoo-guidelines/SKILL.md) for Python and addon code
  outside `static/`.
- [odoo-web-guidelines](../../../community/skills/odoo-web-guidelines/SKILL.md) for JavaScript, Owl,
  SCSS, and frontend tests.
- [odoo-security](../../../community/skills/odoo-security/SKILL.md) when assessing access rights,
  routes, RPC inputs, `sudo()`, or other security-sensitive behavior.
- [odoo-review](../../../community/skills/odoo-review/SKILL.md) for code reviews.
- [odoo-git](../../../community/skills/odoo-git/SKILL.md) for commits and pull requests, with the
  [odoo-git overrides](../../overrides/odoo-git.md).
- [POS_TEST_AGENT.md](../../agents/POS_TEST_AGENT.md) when explicitly asked to write
  or update tests; it defines HOOT/Python/tour selection and coverage scope.

Read only the sources relevant to the task. Architecture exploration does not
authorize adding tests or changing fixtures. The user's explicit instructions
take precedence over conflicting skill recommendations.
