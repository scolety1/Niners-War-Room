# Build Sprint 5H: Cutoff-Approved Snapshot Rebuild

Date: 2026-06-11

Verdict: `SNAPSHOTS_REBUILT_NARROW_PLUS_ROOKIES`

Sprint 5H applies the HQ-approved rookie post-draft cutoff policy and rebuilds local-only legal feature snapshots for eligible row families. It does not train calibrated models, create app percentage values, create player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Cutoff Policy Applied

| Row family | Cutoff policy | Status | Notes |
| --- | --- | --- | --- |
| `all_player_pre_week1` | Fixed `YYYY-09-01` | `eligible_now` | Re-emits the narrow prior-season snapshot set. |
| `rookie_post_draft` | `rookie_post_draft_manifest_approved_v1` | `eligible_now` | 2026 cutoff uses approved factual draft manifest timestamp `2026-05-25T23:45:00+00:00`. |
| `offseason_carryover` | Fixed `YYYY-02-15` | `blocked` | Requires an on-or-before `YYYY-02-15` source snapshot or source availability manifest. |

The rookie post-draft policy admits factual draft manifest fields only. ADP, rankings, public consensus, projections, market values, trade values, RotoWire outlooks/rankings/projections, camp reports, analyst role claims, and non-factual notes remain blocked.

## Sources Used

| Source | Use | Policy |
| --- | --- | --- |
| `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv` | Completed prior-season scoring/first-down features for `all_player_pre_week1` | Prediction-time feature source only when source timestamp is on/before cutoff. |
| `local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/dynastyprocess_db_playerids.csv` | Stable identity/DOB metadata | Stable factual identity metadata; missing or invalid DOB remains missing. |
| `local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv` | Factual rookie draft manifest fields | Approved only under `rookie_post_draft_manifest_approved_v1`. |

## Sources Excluded

The rebuild excludes offseason carryover rows, raw snap counts, RotoWire injury/status context, historical rookie replay context, `player_stats` label supplements, play-by-play label supplements, prior league draft history, projections, rankings, ADP, market sources, trade values, and legacy private scores.

## Row Family Results

| Row family | Attempted | Emitted | Blocked | Result |
| --- | ---: | ---: | ---: | --- |
| `all_player_pre_week1` | 35 | 35 | 0 | Rebuilt and legal. |
| `rookie_post_draft` | 257 | 257 | 0 | Rebuilt under approved manifest cutoff policy. |
| `offseason_carryover` | 35 | 0 | 35 | Blocked by source-after-cutoff policy. |

Total emitted feature snapshots: 292.

## Feature Families Emitted

`all_player_pre_week1` emits:

- `age_at_snapshot`
- `experience_at_snapshot`
- `prior_games_played`
- `prior_rushing_first_downs`
- `prior_receiving_first_downs`
- `prior_receptions`
- `prior_rushing_yards`
- `prior_receiving_yards`
- `prior_passing_yards`

`rookie_post_draft` emits:

- `age_at_snapshot`, where stable DOB metadata is available
- `draft_year`
- `draft_round`
- `draft_pick`
- `draft_day`

Player IDs and player names remain identity/display fields and are not admitted as model features.

## Rookie Manifest Audit

The 2026 rookie manifest passed the approved cutoff policy:

- Source: Kaggle NFL Draft 2026 user download
- Raw source file: `local_exports\model_v4\draft_capital\latest\raw\solution_2026_draft_results.csv`
- Manifest rows: 257
- Collected at: `2026-05-25T23:45:00+00:00`
- Approved cutoff: `2026-05-25T23:45:00+00:00`
- Forbidden field count: 0
- Status: `pass`

## Offseason Carryover Blocker

`offseason_carryover` remains blocked by `blocked_by_source_after_cutoff`.

Required repair:

- obtain an earlier source snapshot on or before `YYYY-02-15`, or
- create and approve a source availability manifest proving the data was available by the cutoff.

The cutoff should not be moved later without changing the business meaning of the row family.

## Legality And Missingness

Legality audit:

- 292 emitted snapshots
- 292 valid
- 0 legality issues
- 0 forbidden-field issues
- 0 supplement-label-source feature issues
- 0 same-season leakage issues

Missingness:

- `age_at_snapshot`: 119 missing out of 292 emitted snapshots
- All other emitted fields are present in the candidate payloads.

Missing optional fields remain missing and are not zero-filled.

## Local Exports

Sprint 5H wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5h_cutoff_approved_snapshot_rebuild/`

Files:

- `cutoff_policy_registry_applied.csv`
- `candidate_prediction_snapshots.csv`
- `candidate_feature_snapshots.csv`
- `row_family_snapshot_readiness.csv`
- `rookie_post_draft_manifest_audit.csv`
- `offseason_carryover_blocker_report.csv`
- `feature_legality_audit.csv`
- `feature_missingness_report.csv`
- `README_SPRINT_5H.md`

## Next Step

Internal-only modeling feasibility can be reassessed with the expanded legal snapshot set, but production/app modeling remains blocked. Before any true calibrated modeling, NWR still needs broader non-enriched rows, stronger out-of-time validation support, confidence/display gates, and a final leakage audit.
