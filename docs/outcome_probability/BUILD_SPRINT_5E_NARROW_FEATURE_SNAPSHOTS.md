# Build Sprint 5E - Narrow Feature Snapshots

## Scope

Sprint 5E built a narrow, local-only feature snapshot scaffold using the Sprint 2 point-in-time contracts and the Sprint 5D-T timestamp decisions. It did not train calibrated models, create app percentages, create player-facing probabilities, create rankings, push, or deploy.

## Readiness Verdict

`FEATURE_SNAPSHOTS_BUILT_PARTIAL`

The narrow builder successfully emitted `all_player_pre_week1` snapshots from timestamp-ready required sources. `offseason_carryover` and `rookie_post_draft` were not materialized because the actual source timestamps did not pass their cutoff requirements.

## Service Added

`src/services/nwr_outcome_feature_snapshot_service.py`

The service builds candidate `FeatureSnapshotCandidate` rows around the existing Sprint 2 concepts:

- `PredictionSnapshot`
- `FeatureSnapshot`
- deterministic `row_id`
- deterministic `snapshot_hash`
- `missingness_mask`
- source manifests
- legality validation

It uses the existing `validate_feature_legality` checks and adds Sprint 5E-specific checks for row-family source eligibility, blocked supplement sources, same-season features, and identity fields.

## Row Families Attempted

| Row family | Status | Emitted | Notes |
| --- | --- | ---: | --- |
| `all_player_pre_week1` | `snapshots_built` | 35 | Built from stable identity metadata plus completed prior-season truth-set scoring fields. |
| `offseason_carryover` | `blocked_by_source_timestamps` | 0 | Truth-set `source_date` is `2026-05-15`, after the `2026-02-15` cutoff. |
| `rookie_post_draft` | `readiness_report_only` | 0 | Draft-capital manifest was collected after the `YYYY-05-01` cutoff, so production-like rookie snapshots were deferred. |

## Sources Used

- `dynastyprocess_db_playerids.csv`
- `truth_set_v3_production_player_season.csv`

## Sources Excluded

- Raw snap counts, because they still need availability timestamp approval.
- RotoWire injury/status context, because it still needs timestamp and quarantine approval.
- Historical rookie replay context, because it still needs leakage review before feature use.
- `player_stats.csv` and play-by-play supplements, because they are label-layer only.
- Prior league draft history, market, projections, ranks, ADP, consensus, legacy private scores, and trade/liquidity context.

## Feature Families Emitted

- Stable identity age metadata.
- Experience derived from stable identity metadata.
- Prior completed-season games played.
- Prior completed-season rushing first downs.
- Prior completed-season receiving first downs.
- Prior completed-season receptions.
- Prior completed-season rushing yards.
- Prior completed-season receiving yards.
- Prior completed-season passing yards.

No player IDs or player names were admitted as model features.

## Local Exports

Local-only exports were written to:

`local_exports/outcome_probability/sprint_5e_narrow_feature_snapshots/`

- `feature_snapshot_manifest.csv`
- `candidate_prediction_snapshots.csv`
- `candidate_feature_snapshots.csv`
- `feature_missingness_report.csv`
- `feature_legality_audit.csv`
- `row_family_snapshot_readiness.csv`
- `README_SPRINT_5E.md`

## Legality Results

The emitted `all_player_pre_week1` snapshots passed legality checks. Blocked/deferred row families were reported in readiness outputs rather than materialized with unsafe timestamps.

The legality policy blocks:

- post-cutoff source timestamps
- same-season final stats as preseason features
- target-window overlap
- forbidden fields
- supplement label sources as prediction features
- unknown/manual-review sources
- player identity fields as model features

## Sprint 5F / Modeling Note

Later internal modeling feasibility can be reassessed after these feature snapshots are reviewed, but production/app modeling remains blocked. The next safe step is an audit of the emitted feature snapshot packet and, separately, timestamp registration for optional sources if richer snapshots are desired.

