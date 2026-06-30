# Rookie Source Availability Reconciliation - 2026-06-30

Verdict: `YELLOW_NO_APPROVED_SOURCES_FOUND`

Master HQ reviewed the current tracked repository artifacts at base HEAD `6bf839a29fc27a21b48b5f53c1e3cbf61548942a` to determine whether any already-approved source can unblock the remaining non-drafted / UDFA watchlist blockers.

## Short Answers

| Blocker question | Answer | Can unblock now? |
|---|---:|---:|
| Approved populated depth chart source? | No | No |
| Approved CFBD identity joins for non-drafted players? | No | No |
| Approved historical UDFA / rookie-free-agent confirmation source? | No | No |

## 1. Approved Populated Depth Chart Source

Answer: no.

Evidence found:

- `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/depth_chart_source_inventory.csv`
  - 5 inventory rows.
  - The only tracked nflverse depth-chart file is a schema/template, not populated data.
- `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_depth_chart_weekly.csv`
  - 0 data rows; header only.
  - Columns include `season`, `week`, `team`, `gsis_id`, `player_name`, `position`, `pos_rank`, and `depth_chart_role_score`.
- `docs/model_v4/ROTOWIRE_DEPTH_CHART_MAY22_SNAPSHOT.md`
  - Documents 727 rows and 32 teams, but the data path is `local_exports/model_v4/depth_charts/latest/rotowire_upcoming_depth_charts_may22.csv`.
  - That path is local/export/vendor-backed and not a tracked safe artifact for this lane.
- `docs/model_v4/ROTOWIRE_LOCAL_SOURCE_CONTRACT_20260608.md`
  - Allows some local RotoWire context only in source-safe pipelines, but the depth-chart rows themselves remain in `local_exports`.

Required question details:

- Source paths: template path above; RotoWire documentation path above.
- Row count: approved tracked populated rows = 0.
- Positions covered: none in approved tracked populated rows.
- Teams covered: none in approved tracked populated rows.
- Player IDs present: yes in template schema, no populated approved rows.
- Depth rank/order present: yes in template schema via `pos_rank`, no populated approved rows.
- Current-only or historical: template is historical-capable schema; no rows. RotoWire doc describes current snapshot only and remains blocked.
- Usable for current review-only watchlist: no.
- Usable for historical modeling: no.
- Blocked because local/export/vendor/private: yes for RotoWire/local_exports rows.

Conclusion: the depth-chart non-drafted watchlist remains empty because no approved tracked populated depth-chart artifact exists.

## 2. Approved CFBD Identity Joins For Non-Drafted Players

Answer: no.

Evidence found:

- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_match_summary.csv`
  - Source rows: 31,822.
  - Candidate rows: 31,827.
  - Exact/high-confidence rows: 157.
  - Possible/low-confidence rows: 46.
  - Ambiguous medium-confidence rows: 5.
  - Unmatched rows: 31,614.
  - Review required: true.
  - Model use allowed: false.
  - Training allowed: false.
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_review_dashboard_summary.csv`
  - Rows requiring human review: 31,822.
  - Rows approved for model use: 0.
  - Draft registry rows: 213.
  - Rows with production context: 5,809 reported in dashboard summary.
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_link_registry_DRAFT.csv`
  - 213 rows.
  - `approved_by_human=false` for all rows.
  - `model_use_allowed=false` for all rows.
  - `training_allowed=false` for all rows.
- `docs/hq/rookie_model/rookie_model_historical_cfbd_and_outcome_backfill_policy_20260630/cfbd_identity_candidate_audit.csv`
  - 17 candidate rows.
  - All 17 have `recommended_status=BLOCKED`.
- `docs/hq/rookie_model/rookie_model_historical_cfbd_and_outcome_backfill_policy_20260630/cfbd_identity_bridge_policy.md`
  - States fuzzy matching cannot approve identities.
  - Historical CFBD identities remain review-only and unapproved for model input.

Required question details:

- Source paths: CFBD identity matching V1 package and historical CFBD backfill policy package above.
- Row count: 31,822 source rows; 31,827 candidate rows; 213 draft registry rows.
- Approved join count: 0 for model/training/source-truth use; 0 human-approved draft registry rows.
- Candidate-only count: at least 213 draft registry rows plus 157 high-confidence review rows, all still review-required.
- Blocked/identity-review-required count: 31,822 source rows require human review; 31,614 unmatched rows; 17 historical candidate audit rows blocked.
- Approval status: review-only / candidate-only / blocked. No model input, no training use.
- Can populate non-drafted high-production watchlist safely: no.

Conclusion: CFBD identity and production context cannot safely populate a high-production non-drafted watchlist yet because no approved non-drafted identity join exists.

## 3. Approved Historical UDFA / Rookie-Free-Agent Confirmation Source

Answer: no.

Evidence found:

- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv`
  - 4,653 rows.
  - drafted: 1,999.
  - confirmed_udfa: 0.
  - likely_udfa_needs_review: 2,514.
  - wrong_universe: 138.
  - name_collision: 2.
- `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/udfa_source_inventory.csv`
  - 10 source inventory rows.
  - Confirms nflverse draft picks can prove drafted status and support draft exclusion.
  - Confirms draft absence and NFL appearance are candidate-only, not confirmed UDFA proof.
- `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/confirmed_udfa_patch_proposal.csv`
  - 0 rows.
- `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/final_udfa_policy_pilot_recommendation.md`
  - likely UDFA rows reviewed: 2,514.
  - confirmed UDFA candidates proposed: 0.
  - still blocked rows: 2,514.
- `docs/hq/rookie_outcomes/udfa_review_application_v1_20260630/udfa_review_application_v1.csv`
  - 38 current-rookie review rows.
  - 28 rows accepted as `confirmed_udfa_review_only`.
  - These are explicitly not model use, training use, source truth, ranking integration, or historical confirmation.

Required question details:

- Source paths: entry-status hygiene packet, UDFA policy pilot packet, current rookie UDFA review application packet.
- Years covered: historical entry-status artifact covers 2000-2024; current rookie review application is current-rookie only.
- Positions covered: QB/RB/WR/TE in the historical entry-status artifact; current review artifact is current rookie review only.
- Direct UDFA/free-agent confirmation: none for historical modeling.
- Possible rookie entry implication: yes, candidate-only through registry/player appearance and draft absence.
- Status: review-only / blocked; no model approval.
- Can promote any `likely_udfa_needs_review` rows to `confirmed_udfa_candidate`: no.

Conclusion: UDFA modeling remains blocked. Draft absence, NFL appearance, Outcome V2 labels, future production, games, starts, AV, awards, seasons played, and fantasy outcomes remain insufficient to prove UDFA entry status.

## Overall Reconciliation

No existing tracked, approved source in HQ unblocks the remaining UDFA/non-drafted blockers. Rookie Data Hygiene does not need to reopen for a hidden available source; it needs a new approved source-ingest/review lane if the user wants to advance UDFA confirmation or depth-chart/high-production watchlists.

Drafted-only Outcome review may proceed separately because drafted rows have factual draft-pick evidence and are not dependent on confirmed UDFA status.

