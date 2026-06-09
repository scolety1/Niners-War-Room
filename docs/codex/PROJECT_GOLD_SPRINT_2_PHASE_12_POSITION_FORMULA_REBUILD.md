# Project Gold Sprint 2 / Phase 12: Position Formula Rebuild

Generated: 2026-05-14

## Status

Complete as a narrow, fixture-backed formula pass. Rankings remain review-only.

## Formula Changes Applied

### QB Elite Exception

Changed the 1QB elite/rushing exception so it can use elite real recent LVE production when independent expected/projection data is neutral or unavailable.

Before:

- Elite exception required strong expected/projection evidence.
- When local baseline projections were neutralized, a secure rushing QB could be suppressed even if actual production and rushing profile were elite.

After:

- The gate still requires strong start security and rushing profile.
- It may use `weighted_recent_lve_ppg_score` as the production signal when expected/projection fields are neutral.
- Generic pocket QBs remain suppressed in 1QB.

Regression fixture added:

- `test_elite_rushing_qb_can_use_real_production_when_projection_is_neutral`

### TE Elite Exception

Changed the no-premium TE elite exception so it can use elite route/target profile plus real production or efficiency when independent projections are neutral.

Before:

- Elite exception leaned on expected/projection evidence.
- Missing independent projections could force every TE into generic no-premium suppression.

After:

- Route role and target earning remain mandatory.
- Strong recent production or efficiency can support the elite exception.
- Low-route TEs remain suppressed.

Regression fixture added:

- `test_elite_te_can_use_real_production_when_projection_is_neutral`

## Formula Changes Deferred

### RB

No RB formula reweight was applied. Existing fixtures already block role-only RB spikes from becoming RB1, and recent audits showed the biggest prior RB/WR imbalance was caused by local baseline projections being treated as independent evidence. That has already been fixed.

### WR

No WR formula reweight was applied. JSN/Tee and other WR disputes are currently source-window and participation/projection problems, not proven formula bugs.

## Active Preview Regeneration

Regenerated review-only preview:

`local_exports/nflverse_model_previews/sprint2_phase12_formula_rebuild_20260514_133016`

Mirrored active stats-first files:

`local_exports/active_veteran_model_public_sources`

Rows:

- normalized rows: 1,039
- preview output rows: 1,039
- outlier rows: 2,994

## Active Preview Notes

The formula patch does not magically fix source gaps. For example, active QBs still show suppressed values where imported role/rushing/participation/projection evidence is weak or stale. That is correct: the new exception only applies when receipts show the required production and role inputs.

Top active preview remains WR-heavy at the top, with Bijan as RB1:

- Justin Jefferson WR1
- CeeDee Lamb WR2
- Ja'Marr Chase WR3
- Brian Thomas Jr. WR8
- Bijan Robinson RB1
- Jahmyr Gibbs RB2

## Verification

Focused formula tests:

- `46 passed`

Full static check is required after this note.
