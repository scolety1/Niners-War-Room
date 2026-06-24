# NWR Unified Player Universe Missing ID + Age Repair

Date: 2026-06-24

Scope: safe data-quality pass on review/prototype artifacts only.

## Verdict

YELLOW-GREEN.

The repair pass reduced missing-age blockers using approved/high-confidence local display-age sources. Missing player IDs were not repaired because no approved high-confidence local source exists for the five remaining rookie/prospect rows.

App wiring remains blocked.

## Starting Counts

- Missing player_id blockers: 5
- Missing age blockers: 42
- Review-needed blockers: 263
- Total remaining blockers: 310

## Ending Counts

- Missing player_id blockers: 5
- Missing age blockers: 16
- Age conflict blockers: 1
- Review-needed blockers: 249
- Total remaining blockers: 271

## Repairs Made

Repair log:

`docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_missing_id_age_repair.csv`

Repair statuses:

- `REPAIRED`: 25
- `NOT_ENOUGH_INFORMATION`: 21
- `CONFLICT_REVIEW_NEEDED`: 1

The 25 repaired rows include:

- 11 rows with age filled from approved/high-confidence display-age sources.
- 14 stale source-layer age blockers removed because the consolidated canonical row already carried a safe display age after duplicate consolidation.

New age fills used:

- `nflverse roster display context display_stat_context_only`
- `DynastyProcess display fallback`
- Existing consolidated canonical display age where the blocker was stale

## Repairs Skipped

Player IDs skipped:

- Sieh Bangura, RB
- Devin Voisin, WR
- Barika Kpeenu, RB
- Braylon James, WR
- Jamarion Miller, RB

Reason:

Existing local identity artifacts classify these as low-confidence/manual-review or `needs_data`. No exact approved high-confidence player_id source was found, so IDs remain blank.

Ages skipped:

- Remaining rookie/prospect age gaps where the age audit showed no DOB coverage or explicit conflict/manual-review status.
- DST rows where player age is not meaningful.

These remain `Not enough information`.

## Conflict

Joshua Palmer, WR has a display-age conflict:

- DynastyProcess display fallback: 26.7
- nflverse roster display context: 26.8

No age was chosen. The row remains `REVIEW_NEEDED` with `age_conflict_review_needed`.

## App Wiring Status

Still blocked.

The review artifact still has:

- 5 missing player_id blockers
- 16 missing-age blockers
- 1 age-conflict blocker
- 249 review-needed rows
- `app_wiring_allowed=no` for all rows
- `model_input_allowed=no` for all rows

## Files Updated

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_remaining_blockers.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_validation_report.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_source_summary.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_missing_id_age_repair.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_missing_id_age_blocker_inspection.csv`

## Recommended Next Step

Run a manual identity review lane for the five missing rookie/prospect IDs and a manual age-review lane for the remaining rookie/prospect/DST age gaps plus the Joshua Palmer conflict. Do not approve app wiring until those blockers are resolved or explicitly accepted as review-only caveats.

## Guardrails

- No app decision pages changed.
- No Dynasty Rankings behavior changed.
- No Drafting Mode behavior changed.
- No model/rank logic changed.
- No Frozen Final Draft Board V1 mutation.
- No `final_board_rank`, Dynasty Rank, tier, latest, or pinned snapshot mutation.
- No fabricated player IDs.
- No fabricated ages.
- No fabricated rookie Dynasty Rank.
- No fabricated outcome probabilities.
- Market/DynastyProcess/ADP remains display-only.
- No `C:\NWR_SHARED_DATA`, `local_exports`, or runtime JSON tracked.
