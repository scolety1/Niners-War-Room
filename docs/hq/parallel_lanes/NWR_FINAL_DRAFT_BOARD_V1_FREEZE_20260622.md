# NWR Final Draft Board V1 Freeze - 2026-06-22

QA verdict: GREEN.

Freeze status: FROZEN_FOR_DRAFT_DAY_REVIEW with HUMAN_REVIEW_REQUIRED.

This freeze records the local-only Final Draft Board V1 package for tomorrow's
human draft review. It does not approve hidden/private-value fields, vendor
source usage, Mock Draft logic changes, hosted deployment, simulations, raw
prediction dumps, or mathematically guaranteed outcomes.

## Frozen Package

Frozen package root:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622`

Frozen board CSV:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`

Frozen workbook:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.xlsx`

Static HTML dashboard:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\index.html`

Zip package:
`C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622.zip`

Freeze timestamp:
`2026-06-21T13:43:42-06:00`

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

## QA Checks

| Check | Result |
| --- | --- |
| Board package exists | PASS |
| Static HTML exists and has no external JS/CSS/assets | PASS |
| Row count documented | PASS |
| Rookies and dropped veterans represented | PASS |
| Unavailable/blocklist overlap excluded unless legal dropped-veteran source applies | PASS |
| QB/RB/WR/TE posture matches required posture | PASS |
| Vendor WR not used as safe signal | PASS |
| No vendor fields in safe board | PASS |
| No ADP/ECR/market/projection/trade-calculator inputs | PASS |
| No `fantasy_points` / `fantasy_points_ppr` input fields | PASS |
| No hidden sort columns | PASS |
| `final_board_rank`, `final_tier`, and `position_rank` visible | PASS |
| Manual review flags visible | PASS |
| Display-only columns labeled display-only | PASS |
| Build manifest exists | PASS |
| Frozen guardrail doc exists | PASS |
| Static HTML states safe use and not-approved boundaries | PASS |
| Pinned snapshot hash unchanged | PASS |
| `latest_candidate` / `latest_approved` untouched | PASS |
| No `C:\NWR_SHARED_DATA` files tracked by Git | PASS |
| No raw vendor files tracked | PASS |
| No Mock Draft logic changed | PASS |

## Model Posture Used

| Position | Posture |
| --- | --- |
| QB | baseline/control |
| RB | `role_usage_core` research evidence |
| TE | baseline/reference |
| WR | `safe_no_snap_no_depth_rank` research evidence |
| WR vendor | excluded; research-only / yellow hold / source-license review required |

## What Is Safe To Use Tomorrow

Use the visible frozen board for human draft-day review:

- `final_board_rank`
- `final_tier`
- `position_rank`
- `model_posture_used`
- `candidate_status`
- `risk_notes`
- `needs_manual_review`

Manual review flags should be read before any human decision.

## What Is Not Approved

This freeze does not approve:

- hidden/private-value fields
- vendor source usage
- WR vendor as a safe model signal
- Mock Draft logic changes
- ADP, ECR, market, projection, or trade-calculator inputs
- raw prediction dumps
- raw vendor rows
- hosted/public access
- mathematically guaranteed outcomes

## Guardrails

The frozen package is local-only and is not committed to the repo. The repo
contains only this summary document. No raw local artifacts, raw vendor rows,
raw prediction dumps, or shared-data files are included in the repository.
