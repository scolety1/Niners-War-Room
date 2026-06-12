# Build Sprint 5D - Feature Source Registration

## Scope

Sprint 5D registered and audited source candidates needed for future legal, point-in-time feature snapshots. This sprint did not build feature snapshots, train calibrated models, create app percentages, create player-facing probabilities, create rankings, push, or deploy.

## Readiness Verdict

`READY_AFTER_TIMESTAMP_REGISTRATION`

Feature snapshot construction is not blocked by source discovery, but it must wait for explicit timestamp/availability registration and cutoff enforcement. Production/app modeling remains blocked.

## Source Registration Results

| Registration status | Count |
| --- | ---: |
| `feature_candidate_after_timestamp_audit` | 10 |
| `feature_candidate_ready` | 1 |
| `label_only` | 5 |
| `manual_review_required` | 5 |
| `reconciliation_only` | 1 |

### Feature Candidate Ready

- `dynastyprocess_db_playerids`: stable identity/DOB metadata. Use for age/DOB metadata and position only after identity joins are validated. DOB is stable factual metadata, but source manifest timestamp should still be recorded.

### Feature Candidates After Timestamp Audit

- `truth_set_v3_production_player_week` and `truth_set_v3_production_player_season`: allowed only for prior NWR finish/PPG, games played/active, and first-down production when the feature builder enforces prior-season or pre-cutoff windows.
- `truth_set_v3_usage_player_week` / `truth_set_v3_usage_player_season`: trailing usage candidates after cutoff/availability timestamp audit.
- `truth_set_v3_snap_share_player_week` / `truth_set_v3_snap_share_player_season`: snap-share and trailing opportunity candidates after cutoff/availability timestamp audit.
- `snap_counts_2022`, `snap_counts_2023`, `snap_counts_2024`: raw snap-count candidates after timestamp and identity checks.
- `rookie_draft_capital_2026`: rookie-post-draft feature candidate only after manifest/cutoff timestamp approval.

### Label-Only Sources

- `truth_set_v3_player_stats`: rare-component label supplement source only. It is not a prediction-time feature source.
- `truth_set_v3_play_by_play_2022`, `truth_set_v3_play_by_play_2023`, `truth_set_v3_play_by_play_2024`: event-date-only rare-component label supplements only. They are not prediction-time feature sources.
- `historical_rookie_outcome_labels`: outcome/label context only unless future work registers legal point-in-time features separately.

### Reconciliation-Only Sources

- `sleeper_nflverse_identity_bridge`: identity reconciliation only.
- `rookie_draft_capital_2026_manifest`: source manifest context only.

### Manual Review Required

- RotoWire factual injury/status context can be useful, but it needs timestamp/source-family review and strict separation from RotoWire projections/rankings/outlooks/values before any feature use.
- Historical rookie replay inputs/outcomes need leakage review. Outcome labels are not predictive features.

### Blocked / Display-Only

- Prior league draft history remains blocked for predictive feature use.
- Projections, rankings, ADP, consensus, market/trade/liquidity context, legacy private scores, and public fantasy totals remain blocked.

## Feature Families Approved or Blocked

### Conditionally Approved
- age/DOB metadata
- draft capital for rookie_post_draft
- first-down production
- games played/games active
- injury/status context if timestamped
- position
- prior NWR finish/PPG
- snap share
- team at cutoff
- trailing usage

These are conditionally approved only when source availability is on or before the prediction cutoff and no same-season final-stat leakage occurs.

### Explicitly Blocked
- ADP
- FantasyPros
- public rankings
- consensus
- startup rankings
- trade calculators
- projections
- RotoWire projections/rankings/outlooks/values
- market rank
- league rank
- prior fantasy draft history
- legacy private_score
- same-season final stats as preseason features
- hindsight notes
- public fantasy totals as labels

## Row-Family Readiness

| Row family | Can Sprint 5E start? | Required sources | Timestamp blockers | Identity blockers | Leakage blockers | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `all_player_pre_week1` | `yes_after_timestamp_registration` | truth_set_v3_production_player_season|dynastyprocess_db_playerids | none | none | none | required sources are present for a narrow feature snapshot build |
| `offseason_carryover` | `yes_after_timestamp_registration` | truth_set_v3_production_player_season|dynastyprocess_db_playerids | none | none | none | required sources are present for a narrow feature snapshot build |
| `rookie_post_draft` | `yes_after_timestamp_registration` | dynastyprocess_db_playerids|rookie_draft_capital_2026 | rookie_draft_capital_2026 | none | none | source set exists, but timestamp/availability registration is still required before feature snapshots |

## Manual Review Queue

The manual review queue is exported to `C:\Dev\niners-war-room\local_exports\outcome_probability\sprint_5d_feature_source_registration\manual_review_queue.csv`.

Main review items:

1. Register source/availability timestamps for truth-set scoring, usage, snap-share, and snap-count feature candidates.
2. Enforce prior-window extraction so same-season final stats never enter preseason features.
3. Keep player_stats/play-by-play as label-layer supplement sources only.
4. Keep prior league draft history and market/projection/rank sources blocked/display-only.
5. Approve or reject rookie draft-capital manifest/cutoff policy before rookie_post_draft feature snapshots.

## Exports

Local-only exports were written to `C:\Dev\niners-war-room\local_exports\outcome_probability\sprint_5d_feature_source_registration`:

- `feature_source_registry.csv`
- `feature_source_audit.csv`
- `row_family_feature_readiness.csv`
- `forbidden_feature_source_audit.csv`
- `manual_review_queue.csv`
- `README_SPRINT_5D.md`

## Sprint 5E Recommendation

Sprint 5E may start only after timestamp registration. Begin with a narrow internal feature snapshot build for `all_player_pre_week1` and `offseason_carryover`; keep `rookie_post_draft` waiting for draft capital source timestamp/manifest approval.

Production/app modeling remains blocked until source registration, legal feature snapshots, out-of-time validation, confidence gates, app display gates, and final leakage audits are complete.
