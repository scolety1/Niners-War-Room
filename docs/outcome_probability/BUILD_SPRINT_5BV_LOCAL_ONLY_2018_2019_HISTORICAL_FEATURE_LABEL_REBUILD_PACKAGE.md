# Sprint 5BV: Local-Only 2018-2019 Historical Feature and Label Rebuild Package

Outcome lane: veteran outcome probability column path only

Verdict: `LOCAL_ONLY_2018_2019_FEATURE_LABEL_ROWS_GENERATED_MODELING_BLOCKED`

Sprint type: `LOCAL_ONLY_ROW_GENERATION_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5BV generated a local-only 2018-2019 historical feature and label rebuild package under the 5BU completed prior-season contract. This sprint did not train models, generate current-pool outcome probabilities, create exact percentages, create coarse bands, create app-readable status/probability/band tables, wire app display, alter rankings/sorting, create hidden sort keys, change rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Evidence used:

- `docs/outcome_probability/BUILD_SPRINT_5BT_FORMAL_2017_2018_COMPLETED_PRIOR_SEASON_REGISTRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BU_LOCAL_ONLY_2018_2019_HISTORICAL_FEATURE_LABEL_REBUILD_PLAN.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Generator:

- `scripts/outcome_probability/build_sprint_5bv_2018_2019_historical_feature_label_rebuild.py`

## 2. Local-Only Package

Package path:

`local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5bv.json` | run metadata, source path, commit, gate status | no |
| `historical_2018_2019_feature_snapshots.csv` | completed prior-season feature snapshots | no |
| `historical_2018_2019_outcome_labels.csv` | target-season labels rebuilt from source-safe NWR components | no |
| `blocked_historical_2018_2019_rows.csv` | blocked/unscored candidate source rows | no |
| `historical_2018_2019_trainability_report.csv` | emitted/blocked row counts and blocker reasons | no |
| `historical_2018_2019_feature_missingness.csv` | feature missingness by season and position | no |
| `historical_2018_2019_label_support.csv` | threshold/tier support counts only | no |
| `historical_2018_2019_legality_audit.csv` | completed-prior-season and leakage checks | no |
| `historical_2018_2019_forbidden_feature_scan.csv` | positive allowlist and forbidden/quarantine scan | no |
| `historical_2018_2019_identity_team_position_audit.csv` | identity, team, and position coverage checks | no |
| `historical_2018_2019_duplicate_key_audit.csv` | source, feature, and label key uniqueness checks | no |
| `historical_2018_2019_population_policy_audit.csv` | veteran, rookie, kicker, blocked, and current-pool policy checks | no |
| `historical_2018_2019_first_down_completeness.csv` | rushing/receiving first-down completeness checks | no |
| `artifact_quarantine_audit.csv` | output quarantine and release-path isolation checks | no |
| `release_blockers.csv` | explicit blockers for modeling, display, sorting, and promotion | no |
| `README_SPRINT_5BV.md` | local package summary and release stance | no |

All generated outputs are marked `internal_only_not_app_readable`.

## 3. Target And Source Mapping

| Target season | Feature source season | Label source season | Result |
| ---: | ---: | ---: | --- |
| 2018 | completed 2017 regular season only | final 2018 regular-season stats only | generated |
| 2019 | completed 2018 regular season only | final 2019 regular-season stats only | generated |

Same-season final target stats were used only as labels. They were not used as preseason prediction features.

## 4. Generated Row Counts

Overall generation:

| Target season | Attempted rows | Feature snapshots | Label rows | Blocked rows | Primary blocker |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2018 | 530 | 377 | 377 | 153 | `blocked_missing_label` |
| 2019 | 550 | 383 | 383 | 167 | `blocked_missing_label` |
| Total | 1080 | 760 | 760 | 320 | `blocked_missing_label` |

Generated label rows by target season and position:

| Target season | QB | RB | WR | TE | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 51 | 98 | 147 | 81 | 377 |
| 2019 | 50 | 94 | 150 | 89 | 383 |
| Total | 101 | 192 | 297 | 170 | 760 |

One 2019 row was blocked for `blocked_source_target_position_mismatch`. All other blocked rows were missing a same-player target-season label row and remain unscored.

## 5. Feature Policy

The package used a positive allowlist of prior-season fields for features. The emitted feature vectors include only completed prior-season source fields:

- `position`
- `prior_completed_season_games`
- `prior_completed_season_games_active`
- `prior_completed_season_games_played`
- `prior_completed_season_passing_yards`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_rushing_yards`
- `prior_season_nwr_finish_rank`
- `prior_season_nwr_ppg`

Fields not approved by the 5BT/5BU source policy were not added to the feature rows. Age and experience were not imputed because the registered player stats input did not provide a source-safe date-of-birth or tenure join for this sprint.

## 6. Label Policy And NWR Scoring Reconstruction

Labels were reconstructed from source-safe target-season components only. The source-safe scoring reconstruction used:

- passing yards divided by 30
- passing touchdowns times 3
- interceptions times -1
- rushing yards times 0.1
- rushing touchdowns times 4
- rushing first downs times 0.4
- receiving yards times 0.1
- receiving touchdowns times 4
- receiving first downs times 0.4
- rushing, receiving, and sack fumbles lost times -1

The package did not copy `fantasy_points`, `fantasy_points_ppr`, projections, rankings, market values, trade values, or label supplement sources into features or labels. Two-point conversion fields and return/special-teams scoring were not used because they were not part of the 5BT/5BU approved source-safe reconstruction surface for this local-only rebuild.

Tier and threshold label support was written only as local diagnostic evidence. No model training or probability calibration was performed.

## 7. First-Down Completeness

First-down completeness passed for both feature-source and label-source seasons:

| Row family | Season | Source rows checked | Missing rushing first downs | Missing receiving first downs |
| --- | ---: | ---: | ---: | ---: |
| feature_source | 2017 | 5125 | 0 | 0 |
| feature_source | 2018 | 5112 | 0 | 0 |
| label_source | 2018 | 5112 | 0 | 0 |
| label_source | 2019 | 5079 | 0 | 0 |

## 8. Identity, Team, Position, And Duplicate-Key Checks

Identity/team/position coverage passed for the audited source and label seasons:

| Row family | Season | Rows checked | Missing player ID | Missing player name | Missing team | Missing position | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| feature_source | 2017 | 5125 | 0 | 0 | 0 | 0 | pass |
| feature_source | 2018 | 5112 | 0 | 0 | 0 | 0 | pass |
| label_source | 2018 | 5112 | 0 | 0 | 0 | 0 | pass |
| label_source | 2019 | 5079 | 0 | 0 | 0 | 0 | pass |

Duplicate-key checks passed:

| Key type | Season scope | Duplicate extra rows | Status |
| --- | --- | ---: | --- |
| source_player_week | 2017 | 0 | pass |
| source_player_week | 2018 | 0 | pass |
| feature_snapshot | 2018-2019 package | 0 | pass |
| label_row | 2018-2019 package | 0 | pass |

## 9. Population Policy

The package includes QB/RB/WR/TE only. Rookies are excluded from veteran heads by requiring a completed prior-season source row before a target-season row can be emitted. Kickers are not applicable and were not modeled. Current 2026 pool rows were not generated or scored.

Blocked rows are carried in `blocked_historical_2018_2019_rows.csv` with `app_release_status=blocked_not_app_readable` and remain unscored.

## 10. Forbidden-Field And Leakage Scan

Forbidden-field scan result: pass.

The positive allowlist excluded non-approved source fields. The generated feature rows do not use:

- ADP
- public rankings
- projections
- consensus
- market values
- trade values/calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- fantasy totals
- EPA
- WOPR/RACR/PACR/Dakota/target-share style fields
- same-season target stats as preseason features
- label supplement sources as prediction features

Leakage-control audit result: pass.

Every emitted row records:

- `source_season_strictly_before_target=yes`
- `same_season_final_stats_as_features=no`
- `label_source_as_prediction_feature=no`
- `fantasy_totals_used=no`
- `legality_status=pass`

## 11. Artifact Quarantine

Artifact quarantine result: pass.

The package is local-only under `local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/`. No app path, release-service path, ranking/sorting path, hidden sort key, promoted artifact path, or app-readable probability/band/status table was created.

The package records these release blockers:

- modeling: `blocked`
- exact percentages: `blocked`
- coarse bands: `blocked`
- app wiring: `blocked`
- rankings/sorting: `blocked`
- hidden sort keys: `blocked`
- promoted artifacts: `blocked`

## 12. Release Stance

Sprint 5BV creates historical rows only. It does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting usage and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but no new app-readable status table was created in this sprint.

## 13. Recommended Next Safe Sprint

Recommended next safe sprint: Sprint 5BW - adversarial audit of the 5BV local-only 2018-2019 historical feature and label rebuild package.

The audit should independently verify:

1. all outputs are internal-only and not app-readable;
2. target/source season mapping is correctly enforced;
3. feature rows contain only completed prior-season fields;
4. labels are reconstructed only from target-season final stats;
5. no forbidden/quarantined fields leak into features;
6. duplicate-key, identity/team/position, first-down, and population policy gates hold;
7. no model training, probabilities, bands, app wiring, rankings/sorting, hidden sort keys, or promoted artifacts were created.
