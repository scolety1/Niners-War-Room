# Project Gold Sprint 1 Checkpoint

Last updated: 2026-05-14

Sprint 1 ends with the model still intentionally review-only. This is the correct state.
The goal of Sprint 1 was not to make rankings decision-ready; it was to stop hidden inputs,
projection defaults, and identity/source assumptions from looking more certain than they are.

## Projection Readiness Report

Current preview source inspected:

`local_exports/nflverse/preview/public_data_20260508_212200/raw`

Current normalized preview timestamp:

`2026-05-14T06:15:22Z`

| projection status | player count | decision meaning |
|---|---:|---|
| independent_projection | 0 | No true external projection source is loaded yet. Projection cannot be treated as independent evidence. |
| local_baseline_projection | 689 | These rows are derived from recent imported nflverse/LVE stats. They are useful context, but not a real forecast. |
| missing_projection | 350 | These normalized players have no projection row matched by player ID. |
| disabled_projection | 0 | No currently inspected rows intentionally disable projection input. |
| normalized players inspected | 1,039 | Active stats-first normalized preview rows in the current public-data snapshot. |

Current projection file note: the active preview `projection_raw_import.csv` was generated
before the Phase 6 schema upgrade, so it does not yet include the physical
`projection_source_status` column. Runtime inference still identifies all 689 projection rows
as `local_baseline_projection` by `projection_scope`, `source_id`, and
`source_scoring_format`. The next preview refresh should regenerate the file with the explicit
column.

## Confidence Impact

| group | average confidence | interpretation |
|---|---:|---|
| players with local baseline projection rows | 79.33 | Confidence is carried mostly by production/role/injury availability, not by independent projection evidence. |
| players missing projection rows | 41.13 | Missing projection rows materially lower confidence and remain visible as review gaps. |

Phase 6 changed the runtime contract so local baselines cannot fill direct expected projection
as if they were an external forecast. Specifically:

- `expected_lve_points_score` neutralizes to 50 unless projection status is `independent_projection`.
- `local_baseline_projection` rows add `local_baseline_projection_not_independent` warnings.
- `disabled_projection` rows neutralize projection features and show `disabled_projection` warnings.
- Non-independent projection rows keep confidence penalties instead of boosting projection confidence.
- Receipts and coverage rows expose `projection_source_status`.

## Do Projection Gaps Block Roster Decisions?

Projection is a review bucket, not a critical roster-decision bucket. Missing or local-baseline
projection inputs should lower confidence and remain visible, but they should not by themselves
block pre-declaration roster decisions.

That said, projection gaps still block final-money confidence if they combine with unresolved
critical source, identity, lifecycle, sanity-fixture, or outlier blockers.

## Hidden Projection Default Check

No hidden projection default is currently allowed to act like real evidence after Phase 6.
Regression coverage now proves:

- missing projections are neutral/imputed, not imported real data;
- local baseline projections cannot fill `expected_lve_points_score`;
- disabled projections cannot fill `expected_lve_points_score`;
- local baseline projections remain visible in receipts and warnings;
- projection source status is included in import, normalization, receipt, and coverage schemas.

## Sprint 1 Completed Fixes

- Model rescue freeze and repeatable audit-packet direction established.
- Data truth contract expanded around real evidence, derived evidence, neutral imputation, manual review, and disabled inputs.
- Hidden default audit made 50/75/76/78-style fallback behavior visible.
- Identity cleanup direction established so stale/ambiguous joins remain review-only.
- Free/public data import coverage documented.
- Paid data trial/value assessment documented.
- Projection layer quarantined so local baseline projections cannot become fake evidence.

## Remaining Blockers

| blocker | current state | next action |
|---|---|---|
| independent projections | none loaded | Use a legal export/API source later, or keep projection optional with retained confidence penalty. |
| current preview schema | generated before Phase 6 column addition | Regenerate public-data preview so `projection_source_status` is physically present in CSVs. |
| role/usage evidence | still proxy-heavy | Sprint 2 should audit and improve role/usage before any formula trust work. |
| age/bio and lifecycle evidence | still needs hard audit | Sprint 2 should verify age/dropoff and young-player bridge inputs. |
| formula trust | not yet unlocked | Do not tune formulas until data truth, role, age, and receipts are audited. |
| final decision gate | still blocked/review-only | Keep rankings review-only until later gate passes. |

## Paid Data Recommendation

Paid data is worth testing only for narrow evidence gaps, not as a shortcut to trust.
The best first trial is still:

1. **Fantasy Points Data Suite**, if legal CSV/API export exists, because it can attack route share, target share, YPRR, role, and usage gaps.
2. **PFF+**, as a manual-export fallback for route/YPRR/usage-style evidence.
3. **FantasyData or SportsDataIO**, if stable API/export and projections/injuries/depth charts become the bigger need.

Do not make FantasyPros the first paid trial. It can help projection context, but it does not solve the most important stats-first role/usage gap.

## Sprint 2 Starting Point

Sprint 2 should start with role/usage and active player truth, not formula rebuilds.
Recommended first Sprint 2 move:

1. Regenerate the current public-data preview with the Phase 6 schema.
2. Audit role/usage rows and source coverage for Niners roster players and top league assets.
3. Audit age/bio and age-dropoff behavior.
4. Only then inspect formula imbalance through receipts.

Rankings remain review-only at this checkpoint.