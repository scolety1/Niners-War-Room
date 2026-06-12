# Build Sprint 5W: Older Player Stats Source Registration

## Scope

Sprint 5W registers and audits older `player_stats.csv` seasons for future historical feature reconstruction. It is source-registration and availability audit work only.

This sprint did not rebuild training rows, train models, run promoted experiments, create app percentages, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote/release any model artifact.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5w_older_player_stats_source_registration/`

Created files:

- `player_stats_season_coverage.csv`
- `player_stats_component_coverage.csv`
- `player_stats_forbidden_field_audit.csv`
- `completed_prior_season_registration.csv`
- `target_season_unlock_impact.csv`
- `manual_review_registration_queue.csv`
- `README_SPRINT_5W.md`

## Source Inspected

Primary source:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Audited seasons:

- 2019
- 2020
- 2021
- 2022
- 2023
- 2024

The source is weekly player stats. Raw duplicate player-season keys are expected because a player has multiple weekly rows before season-level aggregation. For modeled QB/RB/WR/TE rows, no duplicate player-week keys were found in the audited seasons.

## Season Coverage Summary

| Source season | Target preseason | Rows | Regular-season modeled rows | Unique modeled players | Player ID coverage | Position coverage | Registration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2019 | 2020 | 5,261 | 4,875 | 548 | 100% | 100% | `registered_completed_prior_season_fact` |
| 2020 | 2021 | 5,447 | 5,054 | 580 | 100% | 100% | `registered_completed_prior_season_fact` |
| 2021 | 2022 | 5,698 | 5,298 | 595 | 100% | 100% | `registered_completed_prior_season_fact` |
| 2022 | 2023 | 5,631 | 5,252 | 577 | 100% | 100% | `registered_completed_prior_season_fact` |
| 2023 | 2024 | 5,653 | 5,294 | 547 | 100% | 100% | `registered_completed_prior_season_fact` |
| 2024 | 2025 | 5,597 | 5,227 | 562 | 100% | 100% | `registered_completed_prior_season_fact` |

## Registration Policy

For completed prior-season factual stat components:

- Source season: `S`
- Target preseason: `S+1`
- Derived availability date: `S+1-02-15`
- Prediction cutoff: `S+1-09-01`
- Legal only when the source season is strictly before the target season.
- Same-season final stats remain forbidden as preseason features.

The source registration here applies only to completed prior-season factual features for historical reconstruction. It does not admit same-season target stats, label supplement sources as prediction features, imported fantasy totals as labels, market/rank/projection fields, or app/model outputs.

## Allowed Components

The audited source supports the allowlisted completed prior-season components needed for historical snapshots:

- Games played / active games if derived from legal regular-season player-week rows.
- Prior completed-season NWR PPG and finish rank when computed from legal NWR scoring components.
- Rushing first downs.
- Receiving first downs.
- Receptions.
- Rushing yards.
- Receiving yards.
- Passing yards.
- Passing TDs.
- Interceptions.
- Rushing TDs.
- Receiving TDs.
- Fumbles lost, derived from `rushing_fumbles_lost`, `receiving_fumbles_lost`, and `sack_fumbles_lost`.

## Forbidden-Field Audit

The file contains fields that must stay quarantined:

- `fantasy_points`
- `fantasy_points_ppr`
- `passing_epa`
- `rushing_epa`
- `receiving_epa`
- `dakota`
- `pacr`
- `racr`
- `target_share`
- `air_yards_share`
- `wopr`

`fantasy_points` and `fantasy_points_ppr` are excluded as imported fantasy totals/convenience outputs. EPA-style and analytic share columns are audit-only/excluded from prediction features unless a future sprint separately approves them. They are not blockers because the Sprint 5W registration uses a strict allowlist.

No ADP, projection, ranking, market value, trade value, prior fantasy draft history, legacy `private_score`, or RotoWire projection/ranking/outlook/value fields were admitted.

## Completed Prior-Season Registration Result

All audited source seasons were registered as:

`registered_completed_prior_season_fact`

The registration covers source eligibility only. A future rebuild sprint must still rerun feature snapshot legality checks, same-season leakage checks, forbidden-field scans, missingness preservation, deterministic row/hash checks, and local-only export checks.

## Target-Season Unlock Impact

| Target season | Required prior source season | Unlock status |
| --- | ---: | --- |
| 2020 | 2019 | `eligible_for_5x_rebuild` |
| 2021 | 2020 | `eligible_for_5x_rebuild` |
| 2022 | 2021 | `eligible_for_5x_rebuild` |
| 2023 | 2022 | `already_rebuilt_and_registration_compatible` |
| 2024 | 2023 | `already_rebuilt_and_registration_compatible` |

Sprint 5X can start a historical rebuild for 2020, 2021, and 2022, provided it remains local/internal, uses the feature snapshot legality validator, and does not emit app/player-facing outputs.

## Manual Review Queue

No manual review is required for the allowlisted completed prior-season components. The forbidden and analytic convenience fields remain quarantined by policy.

## Verdict

`READY_FOR_5X_2020_2022_REBUILD`

The older `player_stats.csv` seasons can be used as completed prior-season factual sources under the historical availability policy. This unlocks a future Sprint 5X rebuild attempt for 2020, 2021, and 2022 `all_player_pre_week1` historical snapshots.

Production/app modeling remains blocked.

## Confirmed Non-Actions

- No training rows rebuilt.
- No models trained.
- No promoted model experiments run.
- No app percentage values created.
- No public/player-facing probabilities created.
- No rankings created.
- No push or deploy occurred.
- No active app/ranking logic modified.
- No model artifact promoted or released.
