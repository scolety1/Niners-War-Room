# Model v4 Phase 5 Checkpoint And Promotion Decision

Generated: 2026-05-16

## Status

Model v4 remains review-only.

Phase 5 repaired source-scope, evidence visibility, projection handling, and missing-data semantics. It did not promote v4 into the active app rankings, did not unlock readiness gates, and did not mark roster, draft, or final money decisions ready.

## Phase 5 Artifacts

| artifact | purpose |
| --- | --- |
| `docs/model_v4/PHASE_5_EXTERNAL_AUDIT_TRIAGE.md` | Fact-checked the external Phase 4 audit against local files. |
| `docs/model_v4/PHASE_5_MISSING_EVIDENCE_ROOT_CAUSE.md` | Explained why production, first-down, usage, snap, and projection evidence was missing. |
| `docs/model_v4/PHASE_5_SUSPECT_PLAYER_VERIFICATION.md` | Verified audit-named players before changing scores. |
| `docs/model_v4/PHASE_5_PRODUCTION_FIRST_DOWN_IMPORT_REPAIR.md` | Repaired production and first-down imports from structured nflverse rows. |
| `docs/model_v4/PHASE_5_USAGE_SNAP_EVIDENCE_REPAIR.md` | Repaired derived usage and snap-share evidence without treating snap share as route data. |
| `docs/model_v4/PHASE_5_PROJECTION_FIRST_DOWN_STRATEGY.md` | Separated raw-stat projections, recomputed LVE projection points, missing projections, and estimated first-down projections. |
| `docs/model_v4/PHASE_5_WR_NORMALIZATION_AUDIT.md` | Audited elite WR raw inputs, normalized values, and contributions. |
| `docs/model_v4/PHASE_5_VETERAN_MISSING_DATA_PENALTY.md` | Prevented missing veteran evidence from acting like proof of zero value. |
| `docs/model_v4/PHASE_5_MOVEMENT_AUDIT.md` | Compared the regenerated Phase 5 preview to the preserved Phase 4 preview. |

## Summary By Phase

### Phase 5A: External Audit Triage

The external audit was directionally useful but not treated as automatically correct. Confirmed high-impact issues were evidence coverage, missing-data semantics, and WR/RB normalization review. Several audit claims were rejected or narrowed after local verification, including claims that Brock Bowers, Brian Thomas Jr., and Malik Nabers lacked NFL source context in the local 2026 model.

Decision: the audit justified a repair pass, not a blind formula rebuild.

### Phase 5B: Missing Evidence Root Cause

The dominant root cause was a v4 source-scope bug. The review-only preview had been using v3 source reports built for the older 40-player truth set while v4 uses an 80-player truth set.

Key result:

- Missing production rows dropped from 45 to 11 in the source-scope rerun.
- Missing first-down rows dropped from 45 to 11.
- Missing usage rows dropped from 45 to 11.
- Missing snap rows dropped from 45 to 11.
- Projection gaps remained at 42 because the projection source is still the older limited export.

Remaining source gaps are mostly expected young/incoming-player gaps, newer-source-season gaps, or projection-source gaps.

### Phase 5C: Suspect Player Verification

The audit-named suspect players were checked against local identity rows, source rows, component rows, receipts, warnings, lifecycle labels, and teams.

Confirmed clear:

- Chase Brown
- Brock Bowers
- Brian Thomas Jr.
- Malik Nabers
- Jaxon Smith-Njigba
- Puka Nacua

Remaining source-gap or expected-missing cases:

- Saquon Barkley
- Derrick Henry
- Jonathan Taylor
- Davante Adams
- Tyreek Hill
- Travis Kelce
- Luther Burden

Most of the veteran cases are projection-source gaps after source repair, not identity failures. Luther Burden remains a true newer-source-season gap for NFL production, usage, and snap evidence.

### Phase 5D: Production And First-Down Import Repair

The v4 preview now uses structured nflverse production reports generated from the full v4 truth set.

Repair result:

- 69 of 80 truth-set players had covered production and first-down evidence after this phase.
- 34 players were repaired from the old source-scope/import-filter gap.
- Remaining production/first-down missing cases are young/incoming source-season gaps plus one identity alias case that was handled in Phase 5E.

Imported evidence includes passing, rushing, receiving, targets, rushing first downs, receiving first downs, and fumbles lost when present in nflverse data. Rows are marked `imported_real_data` only when sourced.

### Phase 5E: Usage And Snap Evidence Repair

Derived nflverse play-by-play usage and official snap-count imports were repaired for the full truth set.

Repair result:

- 70 of 80 truth-set players had covered usage and snap evidence after this phase.
- Hollywood Brown was repaired through an alias mapping to Marquise Brown for structured source reports.
- 10 players remain missing usage/snap evidence, primarily source-season or incoming-player gaps.

Route data remains explicitly unavailable. The model still does not estimate route participation, routes run, TPRR, or YPRR from snap share.

### Phase 5F: Projection And First-Down Projection Strategy

Projection handling is now explicit and review-only.

Key result:

- 38 players have independent raw-stat projection recomputes.
- 42 players are missing projections.
- 37 players have first-down projections estimated from historical rates.
- 0 players have direct projected first-down rows.

Supplied fantasy point totals remain ignored. LVE projection points are recomputed from raw stat columns. Estimated first downs are labeled `estimated_from_history`, not `direct_first_down_projection`.

### Phase 5G: WR Normalization Audit

The WR audit did not confirm a production or usage normalization math bug.

Key result:

- 9 of 9 requested WRs matched.
- 0 confirmed normalization bug rows.
- 5 formula or data-recency concern rows.
- 9 route-unavailable rows.
- 9 estimated first-down projection rows.

The main WR limitation is not hidden math failure. It is that safe structured production, usage, and snap inputs currently come from 2022-2024 source seasons, while several sanity beliefs rely on newer dynasty context. Route participation and route efficiency remain unavailable in the safe free-data model.

### Phase 5H: Veteran Missing-Data Penalty Repair

Missing established-veteran evidence no longer acts like proof of zero production.

Key result:

- 50 established-veteran rows audited.
- 32 projection-gap rows were adjusted.
- 0 possible import or identity gap rows remained.
- 32 rows now use `evidence_adjusted_missing_not_zero`.
- 0 fake production, projection, injury, route, or market values were created.

Missing projections remain visible and keep confidence in review/weak territory. Not-applicable young-player prior rows no longer show as missing evidence for established veterans.

### Phase 5I: V4 Preview Regeneration And Movement Audit

The regenerated Phase 5 preview was compared against the preserved Phase 4 preview.

Key result:

- 80 rows compared.
- 75 meaningful movement rows.
- 67 large movement rows.
- 6 medium movement rows.
- 40 movements were classified as projection/first-down estimate repair.
- 35 movements were classified as production import repair.

The large movement is expected after repairing the source-scope bug and missing-data semantics, but it also means v4 must be audited again before any promotion.

## Guardrail Confirmation

Current v4 preview summary confirms:

- `active_rankings_overwritten`: false
- `app_promotion`: false
- `decision_ready_unlocked`: false
- `draft_ready_unlocked`: false
- `final_money_ready_unlocked`: false
- `review_status`: review_only
- `preview_output_rows`: 80
- `component_rows`: 640
- `receipt_rows`: 640
- `source_coverage_rows`: 640

Therefore:

- Active rankings are unchanged.
- My Team is unchanged.
- War Board is unchanged.
- No readiness gates were unlocked.
- Model v4 remains review-only unless explicitly promoted later.

## Remaining Risks

### Data Recency

The safe structured nflverse production, usage, and snap evidence in the current preview comes from 2022-2024 source seasons. For players whose 2025 or newer context materially changed their value, v4 still needs fresher structured data before it can be trusted for final decisions.

### Projection Coverage

42 of 80 truth-set players still lack independent raw-stat projections. Missing projections no longer fake low value, but they still limit confidence and make cross-player comparisons less complete.

### First-Down Projections

Direct projected rushing and receiving first downs are unavailable. Estimated first downs are labeled and review-only. This is acceptable for preview work, but it should not be treated as fully independent forecast evidence.

### Route Data

True route participation, routes run, TPRR, and YPRR remain unavailable from safe free/public structured sources. Snap share is only a proxy role signal.

### Formula Balance

After source repair, there are still review concerns about:

- WR projection strength versus stale/limited historical inputs.
- RB versus WR cross-position balance.
- 1QB suppression.
- No-TE-premium suppression.
- Young-player bridge weighting when newer NFL evidence is unavailable.

These are now formula-review questions, not hidden source-scope bugs.

## Promotion Decision

Model v4 is not ready for app promotion.

Model v4 is not ready to replace My Team, War Board, Rankings, Draft Board, or League Targets.

Model v4 is ready for a controlled formula patch pass because the major Phase 5 source-pipeline bugs have been repaired and missing evidence is now represented more honestly.

Recommended next step:

1. Run a formula patch pass against the Phase 5 preview, using receipts and sanity fixtures.
2. Regenerate v4 preview outputs.
3. Run a second external audit packet.
4. Only after that, decide whether app promotion planning is safe.

Do not start app promotion planning before the formula patch pass and second audit.

## Phase 6 Entry Criteria

The next phase may start if:

- Formula changes are made only when backed by receipts, fixtures, and documented football logic.
- Every changed formula has a regression fixture.
- Market and league-rank rule context remain excluded from Dynasty Asset Value.
- Route data remains unavailable unless a licensed structured source is added.
- Missing data remains confidence-lowering or review-only, not zero-value evidence.

## Final Phase 5 Decision

Proceed to formula patch pass.

Do not promote v4 to active rankings.

Do not mark roster decisions ready.

Do not mark draft or final money decisions ready.

Run a second external audit after formula patches and before app promotion.
