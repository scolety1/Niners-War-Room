# Player Detail Card Implementation Plan - 2026-06-09

## Recommended Paths

Component:

- `app/components/player_detail_card.py`

Adapter/helper service:

- `src/services/player_detail_card_service.py`

Tests:

- `tests/test_player_detail_card_docs.py`
- Later implementation tests:
  - `tests/test_player_detail_card_service.py`
  - `tests/test_player_detail_card_component.py`
  - page-level tests for Rankings, Draft Prep, Live Draft Room, and future Roster Decisions.

## Component Boundary

`app/components/player_detail_card.py` should only render a normalized card model. It should not:

- read active data packs directly
- compute private values
- tune formulas
- mutate draft/session state
- infer legal draftability
- create recommendations

It can:

- render common fields
- render page-specific sections supplied by the adapter
- keep receipts collapsed
- display blocked-use disclosures
- display sentinel disclosures

## Service Boundary

`src/services/player_detail_card_service.py` should normalize page rows into a shared card model.

Suggested public functions:

- `build_rankings_player_card(row: Mapping[str, object])`
- `build_draft_prep_player_card(row: Mapping[str, object], *, pick_window: str | None = None)`
- `build_live_draft_room_player_card(row: Mapping[str, object], *, selected_pick: str | None = None)`
- later: `build_roster_decision_player_card(row: Mapping[str, object])`

The service should:

- map field aliases into the common schema
- translate warnings into human-readable data-needed messages
- preserve raw warnings in receipts
- preserve allowed/blocked use
- preserve lineage/source fields
- produce page-specific extension dictionaries
- return explicit `missing_fields` rather than inventing values

## Missing Field Behavior

- Missing strings: `-`
- Missing numeric values: blank or `-`
- Missing source receipts: show `Source receipt unavailable from current row.`
- Missing explanation: `Explanation not available from current source rows.`
- Missing legal draftability: `Legal Pool Pending` or `Needs Source`, not `confirmed_draftable`.
- Missing 2026 5.04 baseline: `No Baseline`, `Manual Watchlist`, `No exact equivalence`.

## Receipts

Receipts must be collapsed by default and include:

- `source_path`
- `source_column`
- `upstream_source_path`
- `upstream_source_column`
- `model_version`
- `lineage_class`
- `allowed_use`
- `blocked_use`
- raw warning flags
- raw source repair notes

## Conservative Language

The component should use review/context language only. It must not render final draft/roster/trade recommendations.

Forbidden strings for tests:

- `Draft this player`
- `Target`
- `Buy`
- `Sell`
- `Cut`
- `Defer`
- `Trade for`

## Migration Sequence

1. Build the normalized dataclass/model and adapter service.
2. Add unit tests for missing-field behavior, warning translation, sentinels, and blocked-use preservation.
3. Build the Streamlit component with static fixture cards.
4. Wire Rankings first, replacing `_render_player_detail` with the shared component while preserving the existing UI behavior.
5. Wire Draft Prep with a selected-row detail surface near the scouting table.
6. Wire Live Draft Room with a selected-row detail surface near Pick Controls / Best Remaining.
7. Wire future Roster Decisions only after that page is unblocked.

## Tests Required Before Wiring Pages

- Common schema supports Rankings, Draft Prep, Live Draft Room, and future Roster Decisions fields.
- Missing fields fail closed.
- Receipts are collapsed/advanced.
- Market/league/prior-history/RotoWire/legacy fields remain display-only or comparison-only.
- Keenan Allen legacy 82.4 and Darius Slayton legacy 78.88 remain comparison-only.
- 2026 5.04 remains no-baseline/manual watchlist/no exact equivalence.
- Outcome percentages remain blank/in development unless a real private model exists.
- No final recommendation language is rendered.
- Existing accepted pages still pass their current smoke/readback tests.

## Skeleton Decision

No component skeleton is created in this task. The accepted pages are stable, and the next step should be a small implementation task with focused tests rather than a hidden partial component that is not yet wired.

## Recommended First Implementation Task

Build `src/services/player_detail_card_service.py` and `app/components/player_detail_card.py` behind fixture tests only. Do not wire pages until the service/component tests pass. Then migrate Rankings first because it already has the richest detail behavior and best sentinel coverage.

