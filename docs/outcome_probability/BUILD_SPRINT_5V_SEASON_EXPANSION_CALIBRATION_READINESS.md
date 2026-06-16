# Build Sprint 5V: Season Expansion Calibration Readiness

## Scope

Sprint 5V is an inventory and planning sprint for NWR Outcome Probability HQ. It does not train models, emit training rows, create calibrated probabilities, create app percentage values, create rankings, push, deploy, or modify active app/ranking logic.

The purpose is to determine what additional historical seasons can be added beyond the current 2023 -> 2024 internal-only diagnostic, and what gates remain before calibration can be reconsidered.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5v_season_expansion_calibration_readiness/`

Created files:

- `candidate_season_inventory.csv`
- `season_expansion_eligibility.csv`
- `source_coverage_by_season.csv`
- `outcome_support_estimate_by_season.csv`
- `calibration_readiness_scenarios.csv`
- `season_expansion_blocker_queue.csv`
- `next_year_label_maturity_audit.csv`
- `README_SPRINT_5V.md`

## Candidate Sources Inspected

The local inventory found the following relevant source families:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
  - 134,470 weekly rows.
  - Covers seasons 1999 through 2024.
  - Contains raw football components useful for labels and prior completed-season features.
  - Also contains quarantined fields such as `fantasy_points`, `fantasy_points_ppr`, and EPA fields. Those remain blocked as predictive features and label shortcuts.
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv`
  - 83 enriched truth-set rows.
  - Covers 2022, 2023, and 2024.
  - Useful as enriched comparison/label context, not a broader universe source.
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`
  - 1,183 enriched weekly truth-set rows.
  - Covers 2022, 2023, and 2024.
- `truth_set_v3_usage_*` and `truth_set_v3_snap_share_*`
  - Cover 2022, 2023, and 2024 for the enriched truth-set universe.
  - Current-source-date status means they require additional review before broader historical feature use.
- `play_by_play_2022.csv.gz`, `play_by_play_2023.csv.gz`, `play_by_play_2024.csv.gz`
  - Event-date-only label supplement candidates.
  - Not prediction-feature-ready.
- `snap_counts_2022.csv`, `snap_counts_2023.csv`, `snap_counts_2024.csv`
  - Raw snap-count candidates requiring identity/timestamp mapping before prediction-feature use.
- `dynastyprocess_db_playerids.csv`
  - Stable identity/DOB metadata candidate.
- Historical rookie outcome files
  - Rookie-only context, not an all-player historical universe source.

## Season Eligibility

| Target season | Current eligibility | Reason |
| --- | --- | --- |
| 2020 | `ready_after_prior_source_registration` | Local raw `player_stats.csv` data exists, but older-season source registration, identity audit, component quarantine, and derived availability approval are still required. |
| 2021 | `ready_after_prior_source_registration` | Same as 2020; local raw data exists, but the legal reconstruction path is not approved. |
| 2022 | `ready_after_prior_source_registration` | Local 2021 prior-season raw data exists, but it needs explicit registration before 2022 pre-Week-1 rows can be rebuilt. |
| 2023 | `ready_for_rebuild` | Already rebuilt in Sprint 5N with 412 trainable rows. |
| 2024 | `ready_for_rebuild` | Already rebuilt in Sprint 5N with 415 trainable rows; next-year starter remains censored. |
| 2025 | `blocked_missing_labels` | Complete mature 2025 labels are not present locally; future windows must remain null/censored, not false. |

## Outcome Support

Measured Sprint 5N support remains the approved baseline for rebuilt rows:

| Outcome | 2023 support | 2024 support |
| --- | ---: | ---: |
| `same_year_difference_maker` | 29 events / 383 non-events | 27 events / 388 non-events |
| `same_year_starter` | 59 / 353 | 58 / 357 |
| `same_year_useful` | 91 / 321 | 91 / 324 |
| `same_year_replacement_or_bust` | 321 / 91 | 324 / 91 |
| `next_year_starter` | 49 / 270, with 93 censored/missing | 0 observed, 415 censored |

Raw `player_stats.csv` estimates suggest 2020, 2021, and 2022 could materially improve event/non-event support, but those are estimates only. No older-season training rows were emitted in this sprint.

## Calibration Readiness

Current 2023/2024 support allows only internal mechanics and aggregate diagnostics. It does not support production/app calibration.

Scenario assessment:

- Current 2023/2024 only:
  - Train/test diagnostic is supported.
  - True calibration holdout is not supported.
  - Rolling-origin validation is not supported.
  - Platt/isotonic calibration remains blocked.
- Add 2022 after source registration:
  - A minimal three-season split may become possible.
  - Calibration feasibility could be reassessed, but not approved automatically.
- Add 2020/2021 after older-season source registration:
  - A stronger rolling-origin and holdout design becomes plausible.
  - Requires explicit source registration, identity audit, and leakage review.
- Add 2025:
  - Blocked until complete mature 2025 labels exist locally.

## Repair Queue

Top blockers before broader calibration work:

1. Register older `player_stats.csv` seasons for historical feature reconstruction.
2. Extend the historical availability policy to 2019-2022 prior completed-season facts.
3. Quarantine blocked fields in `player_stats.csv`, especially `fantasy_points`, `fantasy_points_ppr`, and EPA columns.
4. Validate DynastyProcess/nflverse identity joins for broader older-season universes.
5. Preserve next-year censoring: 2024 and 2025 next-year labels remain unavailable.
6. Run a final leakage audit before any calibrated/app-facing path.

## Verdict

`READY_AFTER_SOURCE_REGISTRATION`

Sprint 5W should not rebuild additional seasons until older `player_stats.csv` seasons are explicitly registered for historical feature reconstruction. The smallest next safe target is likely a 2022 expansion after approving the 2021 prior completed-season source path.

Production/app modeling remains blocked.

## Confirmed Non-Actions

- No calibrated models trained.
- No promoted model experiments run.
- No app percentages created.
- No public/player-facing probabilities created.
- No rankings created.
- No app/ranking logic modified.
- No push or deploy occurred.
