# Project Gold Sprint 2 / Phase 12 Audit: Formula Rebuild Checkpoint

Generated: 2026-05-14

## Status

Sprint 2 ends at a safe review-only checkpoint.

No decision-ready labels were unlocked.

## Fresh Audit Packet

Fresh packet:

`local_exports/model_audits/sprint2_phase12_checkpoint_20260514`

Important files:

- `manifest.json`
- `full_active_rankings.csv`
- `visible_war_board_rankings.csv`
- `niners_roster_rankings.csv`
- `normalized_feature_rows.csv`
- `contribution_receipts.csv`
- `source_coverage_rows.csv`
- `outlier_rows.csv`
- `ranking_movement_vs_model_audit_20260514_072352.csv`
- `named_group_formula_checkpoint.csv`
- `pre_decision_checklist_rows.csv`

The comparison baseline is:

`local_exports/model_audits/model_audit_20260514_072352`

This is the earliest same-shape Sprint 1 style audit packet available on disk.

## Ranking Movement Summary

Compared with `model_audit_20260514_072352`:

| cause | all rows | major movement rows |
|---|---:|---:|
| market isolation | 1,039 | 25 |
| source coverage / confidence policy | 689 | 25 |
| lifecycle labeling | 1,039 | 25 |
| formula change | 57 | 2 |
| age/dropoff | 0 direct baseline movement rows | 0 |
| young bridge | 0 direct baseline movement rows | 0 |
| ranking surface split | 0 direct baseline movement rows | 0 |

Interpretation:

- The biggest visible movements are mostly **not** player-value formula swings.
- Most movement comes from missing market edge being suppressed, confidence/source policy becoming stricter, and lifecycle labels being present in current output.
- The Phase 12 formula change had very small active-preview effects because the current imported QB/TE evidence still does not satisfy the elite exception gates.
- Age/dropoff and young bridge behavior are active in receipts, but they were already present in the baseline audit packet used for this comparison, so they do not show as fresh movement in this particular before/after file.

## Major Movement Examples

The largest rank movers were mostly low/mid rows with near-identical scores:

- Parris Campbell, Dallas Goedert, Cade Otton, Xavier Hutchinson, Robbie Chosen, Kirk Cousins, and Jalen Reagor moved about 41-42 spots down.
- Their private values were essentially unchanged.
- The cause was confidence/source-policy drift, market-edge cleanup, lifecycle labels, and surrounding-row resorting.

This is not an evidence-backed player-value change.

## Named Player Group Audit

Named group export:

`local_exports/model_audits/sprint2_phase12_checkpoint_20260514/named_group_formula_checkpoint.csv`

### Niners Roster Decisions

| player | rank | model value | keeper | status | checkpoint note |
|---|---:|---:|---:|---|---|
| Brian Thomas Jr. | WR8 | 75.81 | 72.49 | data warning | Best Niners model asset; driven by production, target earning, age/bridge context. |
| De'Von Achane | RB6 | 66.14 | 62.94 | model warning | Strong production/role but injury and source gaps keep review status. |
| Kaleb Johnson | RB78 | 53.16 | 48.20 | blocking | Year-one bridge with missing NFL evidence; not decision-safe without review. |
| Lamar Jackson | QB5 | 54.68 | 41.09 | model warning | 1QB/QB suppression remains because active imported evidence does not trigger elite exception. |
| Jayden Higgins | WR95 | 49.75 | 38.11 | blocking | Year-one bridge with missing NFL evidence. |
| Brenton Strange | TE40 | 27.56 | 15.70 | model warning | No-premium TE suppression plus weak route/target profile. |
| Daniel Jones | QB44 | 34.91 | 18.54 | model warning | Replaceable 1QB profile. |

### Elite WRs

Top WRs remain at the top:

- Justin Jefferson WR1
- CeeDee Lamb WR2
- Ja'Marr Chase WR3
- Malik Nabers WR4
- Amon-Ra St. Brown WR5
- Brian Thomas Jr. WR8

Receipt explanation: target earning, role/route proxy, age window, and recent LVE production are the main drivers. Warnings are mostly stale production, missing participation proxy, injury, and missing independent projection.

### Elite RBs And Fragile Older RBs

Top RB order:

- Bijan Robinson RB1
- Jahmyr Gibbs RB2
- Kenneth Walker III RB3
- James Cook RB4
- Najee Harris RB5
- De'Von Achane RB6
- Kyren Williams RB9
- Saquon Barkley RB11

Receipt explanation:

- Bijan/Gibbs are supported by strong production, workload/role, age, and first-down/TD fit.
- Kyren/Saquon/Jacobs carry stronger fragility/age/injury risk, so their model value can look strong while keeper score is capped lower.

### Young Bridge Players

The bridge layer is functioning as review context:

- Brian Thomas Jr. has enough NFL evidence plus bridge support to remain high.
- Kaleb Johnson and Jayden Higgins remain blocking/review because bridge prior is visible but NFL evidence is missing.
- The bridge is not clearing young players as safe just because of draft capital.

### QB/TE Suppression Cases

Active QBs and TEs remain heavily suppressed:

- Josh Allen QB1 is overall rank 232.
- Lamar Jackson QB5 is overall rank 264.
- Brock Bowers TE1 is overall rank 290.

This looks harsh, but it is consistent with the current data state:

- 1QB/3-point passing TD scoring suppresses most QBs.
- No-TE-premium suppresses non-elite TE profiles.
- The active free-data import still lacks independent projections and true participation/route data.
- The new QB/TE elite exceptions only trigger when receipts show the required production, start/route, and role evidence.

## Formula Change Check

Phase 12 changed only:

1. QB elite exception can use real recent production when projections are neutral.
2. TE elite exception can use route/target profile plus real production/efficiency when projections are neutral.

Regression tests were added for both.

No RB or WR formula reweight was applied.

## Remaining Blockers Before Sprint 3

Pre-decision checklist:

| gate | status | detail |
|---|---|---|
| Roster Decisions | review | 13 unaccepted injury review gaps and 232 lower-severity outliers remain. |
| Draft Ready | needs data | Draftable pool / released-veteran workflow is not final. |
| Final Money Decisions | needs data | Final gate remains blocked by draft/data/review readiness. |

Specific remaining blockers:

- 13 injury review gaps need acceptance or better source data.
- 232 lower-severity outliers need review/acceptance or patching if they reveal real bugs.
- Missing independent projections remain a major review-only source limitation.
- Missing participation/route data remains a role/usage limitation.
- Production freshness remains a review issue where current stats do not include the latest completed season.
- Draft pool remains incomplete until released veterans and draftable pool data are final.

## Recommendation For Sprint 3

Sprint 3 should not start with more formula tuning. It should start with:

1. Source gap acceptance or import for injury/projection/participation gaps.
2. Outlier review cleanup.
3. Named player receipt review for the Niners roster.
4. Draft pool data completion.
5. Then a final independent model audit before any decision-ready unlock.

## Verification

Full static check after Phase 12:

- `653 passed`

Rankings remain review-only.
