# Build Sprint 4H: Player Stats Supplement Registration

## Scope

Sprint 4H attempted safe registration of `local_exports/truth_set_lab/v3/downloads/player_stats.csv` as a label-layer rare-component supplement source for limited internal v0 scoring reconstruction.

No calibrated models, player-facing probabilities, app percentages, rankings, push, deploy, or production label recomputation occurred.

## Source Manifest Policy

Recommended policy: `allowed_label_supplement_file_timestamp`.

This registration is only for label/scoring reconstruction supplements. It does not admit `player_stats.csv` as a prediction-time feature source.

| Check | Result |
| --- | --- |
| Source path | `local_exports/truth_set_lab/v3/downloads/player_stats.csv` |
| Row count | 134470 |
| Seasons covered | 1999-2024 |
| Join key | `player_id | season | week` |
| Truth-set matched rows | 1183 |
| Missing player IDs | 0 |
| Duplicate join keys | 1 |
| Team mismatches | 0 |
| Imported fantasy totals present | yes, quarantined |
| Prediction feature ready | no |
| Label supplement ready | yes, after manual approval |

## Timestamp Policy

Decision: `file_timestamp_allowed_for_label_supplement_only`.

`player_stats.csv` does not carry row-level source timestamps. The file modified timestamp and source manifest hash are acceptable only for post-event label-layer supplement use in `limited_truth_set_v0`. They are not acceptable for prediction-time feature rows.

## Field Quarantine

Allowed fields:

- `passing_2pt_conversions`
- `rushing_2pt_conversions`
- `receiving_2pt_conversions`
- `special_teams_tds`

Blocked/quarantined fields include `fantasy_points`, `fantasy_points_ppr`, EPA fields, model-like efficiency fields, projection/ranking/market/ADP contexts, and every field outside the 4H allowlist.

## Duplicate Join-Key Audit

The one duplicate source key is `00-0026498 | 2010 | 8` for Matthew Stafford. It is outside the truth-set row universe. The duplicate appears to split a normal game line from a passing 2PT component row.

Recommended deterministic handling: aggregate only allowed component fields by `player_id | season | week`; keep non-allowed duplicate contexts quarantined. If a future duplicate appears inside the truth-set universe with conflicting allowed components, require manual review.

## Supplement Impact

| Component | Nonzero truth-set rows | Estimated NWR point impact |
| --- | ---: | ---: |
| passing_2pt_conversions | 9 | 18.0 |
| rushing_2pt_conversions | 6 | 12.0 |
| receiving_2pt_conversions | 14 | 28.0 |
| special_teams_tds | 0 | 0.0 |

Total dry-run impact: 58.0 NWR points across 29 truth-set player-week rows. A season label could plausibly change only for a player-season already near a threshold. No labels were recomputed.

## Waiver Decision

For passing, rushing, and receiving 2PT conversions plus special teams TDs: `can_reduce_after_manual_approval` for limited internal v0 label reconstruction.

Return yards, return TDs, fumble recovery TDs, and play-by-play-derived supplements remain future Sprint 4I work.

## Local Outputs

Outputs were written under `local_exports/outcome_probability/sprint_4h_player_stats_supplement_registration/`:

- `player_stats_source_manifest_audit.csv`
- `player_stats_field_quarantine.csv`
- `player_stats_duplicate_join_audit.csv`
- `player_stats_supplement_impact.csv`
- `player_stats_component_waiver_decision.csv`
- `README_SPRINT_4H.md`

## Sprint 5 Status

Sprint 5 remains blocked for calibrated model work. Sprint 4H improves limited v0 label reconstruction readiness but does not create app-ready probabilities or enough breadth for calibrated modeling.
