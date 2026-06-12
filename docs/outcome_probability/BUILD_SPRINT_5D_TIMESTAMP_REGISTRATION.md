# Build Sprint 5D-T - Timestamp Registration

## Scope

Sprint 5D-T resolved timestamp and availability policy for source candidates registered in Sprint 5D. It did not build feature snapshots, train calibrated models, create app percentages, create player-facing probabilities, create rankings, push, or deploy.

## Readiness Verdict

`READY_FOR_FEATURE_SNAPSHOT_BUILD_NARROW`

Sprint 5E can start a narrow feature snapshot build for the listed row families using only timestamp-ready required sources. Optional sources with unresolved availability timestamps must be excluded until registered.

## Timestamp Status Summary

| Timestamp status | Count |
| --- | ---: |
| `blocked` | 1 |
| `file_manifest_timestamp_allowed` | 4 |
| `label_only_timestamp` | 5 |
| `needs_availability_timestamp` | 6 |
| `row_timestamp_ready` | 6 |

## Timestamp Policy By Usage

| Usage | Policy |
| --- | --- |
| prediction-time feature source | Feature values must be available on or before cutoff; current-state overwritten files cannot stand in for historical point-in-time features. |
| post-event label source | May reconstruct labels after outcomes are known; never admit as prediction-time features. |
| stable identity metadata | DOB/identity may be treated as stable factual metadata; keep source manifest and identity validation. |
| reconciliation-only source | Can support joins/manifests; cannot become model features unless separately registered. |
| display-only source | Blocked from predictive features and labels where policy forbids use. |

## Concrete Cutoff Templates

- `all_player_pre_week1`: `YYYY-09-01`
- `offseason_carryover`: `YYYY-02-15`
- `rookie_post_draft`: `YYYY-05-01`

## Row-Family Timestamp Readiness

| Row family | Cutoff | Sprint 5E status | Required timestamp-ready sources | Optional timestamp-ready sources | Missing/manual timestamp sources | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `all_player_pre_week1` | `YYYY-09-01` | `yes_narrow` | dynastyprocess_db_playerids|truth_set_v3_production_player_season | truth_set_v3_usage_player_week|truth_set_v3_usage_player_season|truth_set_v3_snap_share_player_week|truth_set_v3_snap_share_player_season | snap_counts_2022|snap_counts_2023|snap_counts_2024|rotowire_nfl_team_status_review_rows | required sources timestamp-ready; optional sources with timestamp gaps must be excluded until registered |
| `offseason_carryover` | `YYYY-02-15` | `yes_narrow` | dynastyprocess_db_playerids|truth_set_v3_production_player_season | truth_set_v3_usage_player_season|truth_set_v3_snap_share_player_season|truth_set_v3_production_player_week | snap_counts_2022|snap_counts_2023|snap_counts_2024 | required sources timestamp-ready; optional sources with timestamp gaps must be excluded until registered |
| `rookie_post_draft` | `YYYY-05-01` | `yes_narrow` | dynastyprocess_db_playerids|rookie_draft_capital_2026 | none | historical_rookie_replay_baseline_rows|rotowire_cfb_injury_report_2026 | required sources timestamp-ready; optional sources with timestamp gaps must be excluded until registered |

## Source Decisions

- Truth-set v3 production week/season, usage week/season, and snap-share week/season are `row_timestamp_ready` for prior-window feature candidates. The feature builder must enforce source timestamp and cutoff windows.
- DynastyProcess identity/DOB is `file_manifest_timestamp_allowed` for stable identity metadata. DOB is stable factual metadata; keep source manifest and identity validation.
- `player_stats.csv`, play-by-play, and historical outcome labels are `label_only_timestamp`; they are legal for post-event label reconstruction only and blocked from prediction-time feature use.
- Raw snap counts remain `needs_availability_timestamp`; exclude from Sprint 5E narrow build until source availability is registered.
- Draft capital is `file_manifest_timestamp_allowed` for `rookie_post_draft` because the manifest has `collected_at_utc=2026-05-25T23:45:00+00:00` and factual allowed-use. It does not create historical training coverage by itself.
- RotoWire factual injury/status context remains `needs_availability_timestamp` or manual-review for feature use and must stay quarantined from projections/rankings/outlooks.
- Prior league draft history remains `blocked` for predictive feature use.

## Manual Review Queue

Manual review timestamp rows: 6. See `C:\Dev\niners-war-room\local_exports\outcome_probability\sprint_5d_timestamp_registration\manual_review_timestamp_queue.csv`.

## Local Exports

Local-only outputs were written to `C:\Dev\niners-war-room\local_exports\outcome_probability\sprint_5d_timestamp_registration`:

- `timestamp_source_registry.csv`
- `timestamp_policy_by_usage.csv`
- `cutoff_source_availability.csv`
- `row_family_timestamp_readiness.csv`
- `manual_review_timestamp_queue.csv`
- `blocked_timestamp_sources.csv`
- `README_SPRINT_5D_TIMESTAMP.md`

## Sprint 5E Recommendation

Sprint 5E can start as a narrow internal feature snapshot build for `all_player_pre_week1`, `offseason_carryover`, and a narrow `rookie_post_draft` snapshot. It must exclude unresolved optional sources, avoid same-season final-stat leakage, and keep all label-only supplement files out of feature vectors.

Production/app modeling remains blocked until legal feature snapshots exist, out-of-time validation is defined, confidence gates are implemented, app display gates are approved, and final leakage audits pass.
