# NWR Final Draft Board V1 Candidate - 2026-06-22

Status: GREEN for local-only final board candidate build. This is not
`latest_approved`.

This document records the local Final Draft Board V1 Candidate created from the
repaired and post-tune-audited model posture. It does not approve private value,
final rankings, hidden sort, Mock Draft behavior, simulations, deployment,
hosted access, or final draft advice.

## Local-Only Board Package

Board package root:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_candidate_20260622`

Primary board CSV:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_candidate_20260622\FINAL_DRAFT_BOARD_V1_CANDIDATE.csv`

Workbook:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_candidate_20260622\FINAL_DRAFT_BOARD_V1_CANDIDATE.xlsx`

Static local dashboard:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_candidate_20260622\index.html`

The package is local-only and is not committed to the repository.

## Board Summary

| Item | Value |
| --- | ---: |
| Board rows | 66 |
| Rookie rows | 54 |
| Dropped-veteran rows | 12 |
| Manual-review flags | 36 |
| QB rows | 3 |
| RB rows | 22 |
| WR rows | 38 |
| TE rows | 3 |

The 66 rows match the pinned snapshot validation count for the available pool.
The board combines the frozen rookie mock input with the pinned legal
dropped-veteran pool and respects the pinned unavailable/blocklist package.

## Source Inputs Used

- Repaired model package:
  `C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622_repaired`
- Post-tune forensic audit:
  `C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622_repaired\post_tune_forensic_audit_20260622`
- Draft-day review export:
  `C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_review_package_20260622`
- Pinned snapshot:
  `C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1`
- Frozen rookie pool:
  `C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\20260620_065435_stripped_candidate\rookie_2026_mock_draft_input.csv`
- Dropped-veteran pool:
  `C:\NWR_SHARED_DATA\lane_exchange\drop_decision\dropped_veterans\20260620_131511_identity_normalized_live_test\dropped_veterans.csv`
- Unavailable/blocklist package:
  `C:\NWR_SHARED_DATA\lane_exchange\drop_decision\unavailable_players\20260620_132700_brian_thomas_conflict_live_test\unavailable_players.csv`
- Pinned veteran candidate value evidence:
  `C:\NWR_SHARED_DATA\lane_exchange\model_value\veteran_private_values\20260620_1535_nobom_live_test\veteran_private_values_candidate.csv`

## Model Posture Used

| Position | Model posture used | Candidate status |
| --- | --- | --- |
| QB | baseline/control | baseline/control preferred |
| RB | `role_usage_core` | research candidate evidence only |
| TE | baseline/reference | baseline/reference preferred |
| WR | `safe_no_snap_no_depth_rank` | research candidate evidence only |
| WR vendor | excluded | research-only / yellow hold / source-license review required |

## Visible Ranking Fields

The board includes visible rank and ordering fields only:

- `final_board_rank`
- `final_tier`
- `position_rank`
- `final_board_score_visible`
- `score_basis_visible`

No hidden sort fields are included. The score basis is visible for every row:
rookies use a candidate score mapped from frozen rookie rank and tier; dropped
veterans use pinned veteran candidate value evidence for the legal dropped pool.
This remains a board candidate and is not final private-value approval.

## Display-Only Fields

Display-only context fields are explicitly labeled in the board:

- `rookie_rank_display_only`
- `rookie_tier_display_only`
- `draft_action_display_only`
- `warning_severity_display_only`
- `nfl_draft_capital_display_only`
- `depth_chart_role_display_only`
- `veteran_candidate_value_display_only`
- `veteran_candidate_rank_display_only`
- `veteran_trust_status_display_only`

No ADP, ECR, market, projection, trade-calculator, vendor, raw prediction, or
raw vendor fields are used in the safe final board.

## Manual-Review Caveats

Manual-review flags are carried forward into:
`FINAL_DRAFT_BOARD_V1_MANUAL_REVIEW_FLAGS.csv`

Flags include rookie warning severity/manual questions, unknown veteran team
status, and veteran trust warnings. These are review prompts only and do not
approve final draft advice.

## Guardrails

- `latest_approved` was not updated.
- Pinned snapshot was not mutated.
- Mock Draft logic was not changed.
- No deployment, hosted/public access, or exposed ports were created.
- Vendor research fields were excluded from the safe board.
- Raw vendor CSVs and raw prediction dumps were not committed.
- `C:\NWR_SHARED_DATA` contents were not committed.

## Next Step

Run a Final Board QA/freeze gate before any `latest_approved` action. That gate
should verify board construction, visible sort fields, unavailable-player
handling, manual-review flags, and approval language before Tim treats the board
as usable final draft-day rankings.
