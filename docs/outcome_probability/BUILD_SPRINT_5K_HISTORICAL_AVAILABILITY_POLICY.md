# Build Sprint 5K: Historical Availability Policy

Date: 2026-06-11

Verdict: `READY_FOR_5L_HISTORICAL_REBUILD`

Sprint 5K defines when later-collected local files can be used to reconstruct older point-in-time feature snapshots. It does not build calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Why This Policy Exists

Sprint 5J attempted historical `all_player_pre_week1` snapshots for 2022, 2023, and 2024. It emitted 0 legal snapshots because the current local truth-set file carries `source_date=2026-05-15`, after each historical `YYYY-09-01` cutoff.

That late local collection timestamp does not automatically mean the underlying completed prior-season fact was unknowable before the historical cutoff. It does mean NWR needs an explicit derived-availability policy before using those facts in point-in-time reconstruction.

## Timestamp Concepts

| Concept | Meaning | Policy use |
| --- | --- | --- |
| `event_date` | Date the underlying football event happened. | Useful context, but not enough by itself for prediction-time feature availability. |
| `source_collection_timestamp` | Date/time NWR collected or generated the local file. | Hard availability bound when no derived availability policy exists. |
| `derived_availability_date` | Conservative as-of date assigned to a historical fact family. | Allowed only for explicitly approved source families. |
| `input_snapshot_date` | Prediction cutoff for a feature row. | Feature availability must be on or before this date. |
| `source_max_timestamp` | Latest availability timestamp among feature sources in one row. | Must be `<= input_snapshot_date`. |
| `label_available_date` | Date after which the outcome label is mature and observable. | Training rows may materialize only after this date. |

## Source-Family Classifications

| Source family | Classification | Derived availability | Allowed use |
| --- | --- | --- | --- |
| `truth_set_completed_prior_nwr_stats` | `completed_prior_season_stat` | yes | Prediction-time feature after prior season is finalized. |
| `dynastyprocess_identity_dob` | `stable_identity_metadata` | yes | Stable DOB/identity metadata with manifest and identity validation. |
| `truth_set_target_season_stats` | `post_event_label_source` | label-only | Label reconstruction only; never same-season preseason features. |
| `usage_snap_share_current_exports` | `current_state_snapshot` | no | Manual review or future timestamped feature source only. |
| `player_stats_and_pbp_supplements` | `post_event_label_source` | label-only | Rare-component label reconstruction only. |
| `rookie_draft_manifest_factual` | `reconstructable_historical_fact` | season manifest only | Factual rookie draft features after approved manifest timestamp. |
| `rotowire_rank_projection_market_context` | `blocked` | no | Excluded regardless of timestamp. |

## Derived Availability Templates

| Template | Status | Rule |
| --- | --- | --- |
| `completed_prior_season_stats_available_feb15_v1` | allowed | Completed prior-season factual NWR stat components for season `S` may be treated as available no later than `S+1-02-15`, if target season `Y >= S+1` and source fields are audited factual components. |
| `stable_identity_metadata_manifest_v1` | allowed with identity manifest | DOB and immutable identity may be used as stable factual metadata; missing DOB remains missing. |
| `rookie_manifest_approved_timestamp_v1` | allowed after manifest approval | Factual draft fields are available only at or after the approved season-specific draft manifest timestamp. |
| `same_season_stats_feature_block_v1` | blocked | Target-season final stats are labels after maturity, never preseason features for that same season. |
| `current_state_overwritten_source_block_v1` | blocked until availability manifest | Current-state overwritten files cannot be backdated without historical as-of evidence. |

## Guardrails

The derived-availability policy does not admit:

- target-season final stats as preseason features
- same-season target labels as features
- public fantasy totals as labels
- ADP, FantasyPros, public rankings, consensus, startup rankings, trade calculators
- projections or projected fantasy points
- RotoWire projections/rankings/outlooks/values
- market rank, league rank, trade values
- prior fantasy draft history
- legacy `private_score`
- hindsight notes
- label supplement sources as prediction features

Timestamp cannot cleanse a forbidden source family.

## Re-Audited Sprint 5J Blockers

Sprint 5K re-audited all 83 Sprint 5J blocked historical rows.

| Re-audited status | Count |
| --- | ---: |
| `eligible_after_derived_availability_policy` | 48 |
| `still_blocked_missing_prior_source` | 35 |

By target season:

| Target season | 5J rows | Eligible after policy | Still blocked missing prior source |
| --- | ---: | ---: | ---: |
| 2022 | 20 | 0 | 20 |
| 2023 | 28 | 20 | 8 |
| 2024 | 35 | 28 | 7 |

Rows eligible after policy were previously blocked only because the file collection timestamp was after cutoff. Under `completed_prior_season_stats_available_feb15_v1`, completed prior-season factual stat components can receive a derived availability date before the target season pre-week-1 cutoff.

Rows still blocked have no completed prior-season source row in the local truth-set. The policy cannot invent missing prior data.

## Historical Snapshot Rebuild Eligibility

Sprint 5L can start a partial historical rebuild for eligible rows only:

- 2023: 20 eligible rows
- 2024: 28 eligible rows
- 2022: no eligible rows until 2021 prior-season source data exists

Expected Sprint 5L behavior:

- emit only rows that pass derived-availability and missing-prior checks
- preserve blocked rows in audit outputs
- keep same-season final stats out of feature vectors
- link mature labels only after feature legality passes
- produce local-only outputs

## Manual Review Queue

Manual review remains for:

- current-state usage/snap-share exports, which need historical as-of snapshots or availability manifests before feature use
- historical rookie draft manifest availability, if future historical rookie post-draft snapshots are desired

## Local Exports

Sprint 5K wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5k_historical_availability_policy/`

Files:

- `timestamp_concepts.csv`
- `historical_availability_policy.csv`
- `source_family_availability_classification.csv`
- `derived_availability_templates.csv`
- `re_audited_5j_blockers.csv`
- `historical_snapshot_rebuild_eligibility.csv`
- `manual_review_availability_queue.csv`
- `README_SPRINT_5K.md`

## Remaining Blockers Before True Calibrated Modeling

- Sprint 5L must rebuild and audit the eligible historical feature snapshots.
- Missing-prior rows remain unavailable until prior-season sources exist.
- Broader non-enriched rows are still needed.
- Out-of-time validation support is still weak.
- Confidence/display gates and final leakage audit are still required.
- Production/app modeling remains blocked.
