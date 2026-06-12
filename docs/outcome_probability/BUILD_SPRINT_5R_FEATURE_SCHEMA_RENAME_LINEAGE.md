# Build Sprint 5R: Feature Schema Rename Lineage

Status: `FEATURE_SCHEMA_RENAMED_WITH_LINEAGE`

Sprint 5R applied the Sprint 5Q feature legality decision by renaming ambiguous prior-production features and carrying explicit lineage metadata through the feature snapshot contract.

This sprint did not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote/release a model artifact.

## Scope

Sprint 5Q found that prior-production features were legal for internal mechanics only when they were clearly identified as completed prior-season facts. Sprint 5R turns that review into schema cleanup for future feature snapshots and future internal modeling experiments.

The schema cleanup applies to the feature snapshot builder and test contract. Sprint 5P model mechanics were not rerun; the 5P experiment remains valid after feature rename because this sprint changes feature names and lineage metadata, not model outputs.

## Feature Renames

Required before future training:

| Old feature | New feature |
| --- | --- |
| `prior_nwr_ppg` | `prior_season_nwr_ppg` |
| `prior_nwr_finish_rank` | `prior_season_nwr_finish_rank` |

Recommended completed-prior-season cleanup:

| Old feature | New feature |
| --- | --- |
| `prior_games` | `prior_completed_season_games` |
| `prior_games_played` | `prior_completed_season_games_played` |
| `prior_games_active` | `prior_completed_season_games_active` |
| `prior_rushing_first_downs` | `prior_completed_season_rushing_first_downs` |
| `prior_receiving_first_downs` | `prior_completed_season_receiving_first_downs` |
| `prior_receptions` | `prior_completed_season_receptions` |
| `prior_rushing_yards` | `prior_completed_season_rushing_yards` |
| `prior_receiving_yards` | `prior_completed_season_receiving_yards` |
| `prior_passing_yards` | `prior_completed_season_passing_yards` |

The feature snapshot builder now canonicalizes old ambiguous names to these new names before it builds the emitted `feature_vector`.

## Lineage Metadata

Every emitted feature snapshot candidate now carries a `feature_lineage` payload keyed by feature name. For renamed prior-production features, lineage metadata includes:

- source season
- target season
- derived availability date
- prediction cutoff
- feature family
- legality status
- source manifest or source policy id
- source season strictly before target flag
- derived availability before cutoff flag
- target-window overlap flag
- same-season final stat leakage flag
- label supplement source as feature flag
- notes

For completed prior-season features, the controlling source policy is:

`completed_prior_season_stats_available_feb15_v1`

The lineage contract proves:

- source season is strictly before target season
- derived availability date is before the prediction cutoff
- there is no target-window overlap
- there is no same-season final stat leakage
- label supplement sources are not used as prediction features

## Service Changes

Updated:

- `src/services/nwr_outcome_feature_snapshot_service.py`

Key changes:

- Added `FEATURE_RENAME_MAP`.
- Added canonical feature-name handling in `build_feature_snapshot_candidate`.
- Added `feature_lineage` to `FeatureSnapshotCandidate`.
- Added lineage metadata generation for each candidate feature.
- Updated current all-player feature construction to emit completed-prior-season names directly.
- Updated feature snapshot CSV exports to include serialized `feature_lineage`.

## Test Changes

Updated:

- `tests/test_nwr_outcome_feature_snapshot_service.py`

Added coverage verifies:

- old ambiguous prior names are not emitted in new feature vectors
- renamed features are emitted
- lineage metadata exists for renamed features
- source season is before target season
- derived availability is before cutoff
- same-season feature blocking still holds
- label supplement sources remain blocked as features

## Local Outputs

Sprint 5R wrote local-only exports under:

`local_exports/outcome_probability/sprint_5r_feature_schema_rename_lineage/`

Created outputs:

- `feature_rename_map.csv`
- `feature_lineage_contract.csv`
- `renamed_feature_snapshot_sample.csv`
- `feature_schema_compatibility_report.csv`
- `README_SPRINT_5R.md`

Compatibility summary:

- 827 prior Sprint 5N rows inspected through the rename layer
- 7,443 old ambiguous feature occurrences mapped forward
- old ambiguous names absent after rename: `pass`
- renamed feature occurrences represented after rename: `pass`
- feature lineage metadata present in sample rows: `pass`
- Sprint 5P validity: `valid_after_feature_rename`

## Compatibility Notes

Backwards compatibility is limited to canonicalization. If a caller still provides an old ambiguous feature name, the feature snapshot builder maps it to the new completed-prior-season name before emission. Future outputs should use the new names directly.

Sprint 5P internal mechanics remain valid under the renamed schema. Any future internal modeling experiment should consume the renamed feature names only and should carry lineage metadata forward.

## Still Blocked

The following remain blocked as prediction-time features:

- same-season final stats
- target-window labels
- future-window labels
- public fantasy totals
- ADP, public rankings, projections, consensus, market values, trade values, prior fantasy draft history, and legacy `private_score`
- label supplement sources as prediction features

## Readiness

Future internal modeling may continue after consuming the renamed feature schema and preserving lineage metadata.

Production/app modeling remains blocked pending:

- final leakage audit
- more seasons and validation support
- calibration and confidence gates
- app display gate
- explicit HQ approval before any promoted model artifact or player-facing output

## Safety Confirmation

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
