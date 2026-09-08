# Diggs-Class Source-Gap Fix — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 4 ("Brooks/Diggs-class
source-gap repair — systemic, not by name"). Root cause originally identified in
`docs/codex/NWR_BROOKS_DIGGS_JUDKINS_ROOT_CAUSE_V1_20260908.md`.

## Problem

`build_current_projection_candidate()`'s acquisition-stage universe filter
(`src/services/redraft_2026_projection_model_service.py`) required
`players["last_season"].eq(season)`. A real, currently active player (`status=ACT`) whose most
recent RECORDED stat line is one real season behind (injury, opt-out, or simply that the new
season hasn't started) was silently excluded from the entire admitted universe. Verified real
case: Stefon Diggs, `status=ACT`, `last_season=2025`, excluded from the 2026 build's 910-row
universe entirely.

## Fix, iteration 1 (widening only)

Changed the filter to `players["last_season"].between(season - 1, season)`, kept
`players["status"].isin(("ACT", "RES"))` as the safety valve. Real before/after audit against
the exact snapshot the live build reads
(`source_snapshots/nflverse/players/20260730T072407Z-42af9666ac84/raw/players.parquet`):
OLD universe = 910, unguarded NEW universe = 985 (+75).

## Real false-positive risk found during the required audit

Some newly-admitted names showed `status=ACT` in BOTH the static July-30 snapshot and a live,
current `nflreadpy` re-query — e.g. **Philip Rivers** (retired after the 2020 season) and
**Russell Wilson**. This means nflverse's `players` registry `status` field does not reliably
track real retirement for every player (it appears to freeze rather than update in some cases),
so the plain one-year widening genuinely risked re-admitting real long-retired players alongside
the intended real active-but-injured ones.

## Fix, iteration 2 (roster cross-check — final)

Cross-checked the same real gsis_id identities against a *different*, more granular, already
locally-staged nflverse table from the same 2026-07-30 acquisition batch:
`source_snapshots/nflverse/seasonal_rosters/20260730T072407Z-e550f5d52c60/raw/seasonal_rosters_2025.parquet`
(`nfl.load_rosters(seasons=[2025])` equivalent — verified identical against a live re-pull).
This table's own `status` column (`ACT`/`RES`/`DEV`/`CUT`/`INA`/`RET`/`TRD`/`TRC`) is a real,
different signal ("final roster status for the season," not "most recent season with a recorded
stat line") — verified directly: Rivers and Wilson show `INA` there, while every genuinely
current player checked (Diggs, Hill, Allen, Chubb, Garoppolo, Deebo Samuel Sr.) shows `ACT`/`RES`.

Implementation (`build_current_projection_candidate`, optional `roster_status_by_gsis_id`
parameter, joined by canonical `gsis_id` — never by display name, avoiding the real
"Deebo Samuel" vs "Deebo Samuel Sr." suffix mismatch found while investigating this):

- Applies **only** to the newly-widened `last_season == season - 1` slice. The original,
  already-correct `last_season == season` admissions are never touched.
- Excludes a row only if its real roster status is one of `NOT_CURRENTLY_ROSTERED_STATUSES =
  {"INA", "RET", "CUT"}`.
- A gsis_id with **no** entry in the roster snapshot is kept (missing coverage is not treated
  as evidence of retirement — real coverage on the widened slice measured at 100%, see below,
  so this fallback did not need to be exercised in the real run).
- Backward compatible: omitting the parameter (default `None`) reproduces the unguarded
  widening exactly (no behavior change for any existing caller that doesn't pass it).

`scripts/build_redraft_2026_projection_admission_packet.py` (the real production caller) now
loads this same real, already-staged roster snapshot and passes it through by default
(`DEFAULT_ROSTER_SNAPSHOT`).

## Real, final before/after audit

```
OLD universe (last_season==season):          910
NEW universe UNGUARDED (season-1..season):    985
NEW universe GUARDED (roster cross-check):    973
Real false-positives caught & excluded:        12
Net newly admitted vs OLD:                     63
Widened-slice roster-snapshot coverage:      75/75 (100.0%)
```

12 real false positives excluded, all verified genuinely `INA` on the real 2025 roster
snapshot: Chase Edmonds, Malik Heath, Jakobie Keeney-James, Raheem Mostert, Desmond Ridder,
**Philip Rivers**, Cooper Rush, Brett Rypien, Sterling Shepard, Casey Washington, **Russell
Wilson**, John Wolford.

63 real players newly, correctly admitted, including every previously-identified SOURCE_GAP
name: Stefon Diggs, Tyreek Hill, Deebo Samuel Sr., Keenan Allen, Najee Harris, DeAndre Hopkins,
Darren Waller, Zach Ertz, Jimmy Garoppolo, Nick Chubb, plus 53 further real depth/veteran
players (Brandin Cooks, Austin Ekeler, Gabe Davis, Rondale Moore, Adam Thielen, etc.).

## Tests

4 new tests added to `tests/test_redraft_2026_projection_model_service.py`:
- `test_last_season_one_year_widening_admits_a_real_active_player_diggs_class`
- `test_roster_status_cross_check_excludes_a_real_retired_player_rivers_class`
- `test_roster_status_cross_check_never_touches_the_unwidened_current_season_slice`
- `test_roster_status_cross_check_keeps_players_with_no_roster_snapshot_entry`

A genuine, pre-existing latent bug was also found and fixed while adding these tests:
`blocked_frame`/`identity_frame` construction (`pd.DataFrame(list)` with no explicit `columns=`)
raised `KeyError` on `.sort_values(["position", ...])` whenever the list was empty — previously
unreachable because no caller had ever driven `universe` to zero rows for a call; the new
roster cross-check is the first real code path that can. Fixed by passing explicit `columns=`
(content/order unchanged for the non-empty case).

Full regression: `test_redraft_2026_projection_model_service.py` 7/7,
`test_shadow_numeric_authorities_service.py` 53/53, `test_decision_bundle_service.py` all pass
(77 total across the three files). Both real boards (403 N 18th, Fantasy Gamers) re-verified
byte-identical (same `updated_at_utc`, same pick counts) before and after this unit.

## Status

Diggs-class fix: **DONE**, committed. Brooks-class fix (existing-infrastructure reuse for
players who pass this universe filter but lack a usable prior-season stat line, e.g. rookies-
with-partial-history) is the next unit in Section 4.
