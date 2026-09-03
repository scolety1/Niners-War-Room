# Historical adapter — explicit BLOCKED_* status codes (section 20)

Extends `src/services/historical_replay_data_adapter_service.py`
(section 18's original adapter, still not imported by
`desktop_facade.py` or any frontend page). Tests:
`tests/test_historical_replay_data_adapter_service.py`, 32/32 passing
(12 new). Fixtures remain small, explicitly-synthetic rows built only to
exercise adapter mechanics — never presented as real historical
evidence, since no real dataset exists in this repo yet.

## New checks

- `find_duplicate_player_seasons`: flags any `(player_id, season)` pair
  appearing more than once — an ambiguous ranking-input row, not a real
  second season.
- `find_immature_outcome_rows`: flags a row whose `outcome_as_of` falls
  short of `MATURITY_MIN_DAYS_AFTER_DRAFT` (140, a disclosed round-number
  floor — not calibrated, since no real dataset exists to calibrate it
  against) past `draft_date` — a real but not-yet-final outcome
  snapshot, so it isn't silently used as if the season were over. A row
  with no `outcome_as_of` at all (pre-draft-only) is not flagged.

## `validate_historical_dataset`: one explicit status, not a bare boolean

Runs schema, identity (when `historical_picks` is supplied), leakage,
duplicate-player-season, and outcome-maturity checks, and reduces them
to exactly one of `DATASET_VALIDATION_STATUSES`:
`OK` / `BLOCKED_SCHEMA` / `BLOCKED_IDENTITY` / `BLOCKED_LEAKAGE` /
`BLOCKED_DUPLICATE_PLAYER_SEASON` / `BLOCKED_IMMATURE_OUTCOME`, in that
fixed priority order (schema first — nothing else is meaningful to
check once the row shape itself is wrong). The full detail from every
individual check is still attached to the result, not discarded once a
status is chosen.

"Train/validation/test chronology" (the directive's own named category)
is `chronological_split`'s existing strictly-earlier enforcement
(section 18, already tested) — re-asserted here as the named outcome for
that scenario category rather than duplicated into a new function.

## What this proves, and what it does not

Every `BLOCKED_*` status is demonstrated against a real, minimal
synthetic case (missing/invalid field shape, a leakage-shaped column, a
literal duplicate row, an outcome dated too soon after the draft, an
unresolved historical pick, and a non-chronological split request) — the
mechanics are proven correct. This does not mean real historical data is
now usable: the substrate gap
(`docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md`) is
unchanged — the goal, per the directive, is that when real data does
arrive, this adapter is immediately ready rather than needing a design
pass first.
