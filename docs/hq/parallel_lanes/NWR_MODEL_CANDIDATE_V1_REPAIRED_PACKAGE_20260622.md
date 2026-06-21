# NWR Model Candidate V1 Repaired Package - 2026-06-22

Status: GREEN for local-only repaired research package. No model is approved.

This document records the repaired Model Candidate V1 research package after
removing the blocked `depth_chart_best_rank` feature from the WR safe path. It
does not approve private value, rankings, hidden sort, Mock Draft behavior,
simulations, final draft advice, deployment, `latest_candidate`, or
`latest_approved`.

## Local-Only Repaired Package

Package root:
`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622_repaired`

Required local-only files created:

- `MODEL_CANDIDATE_V1_REPAIRED_MANIFEST.csv`
- `MODEL_CANDIDATE_V1_REPAIRED_BY_POSITION.csv`
- `MODEL_CANDIDATE_V1_REPAIRED_FEATURES.csv`
- `MODEL_CANDIDATE_V1_REPAIRED_METRICS.csv`
- `MODEL_CANDIDATE_V1_REPAIRED_YEARLY_STABILITY.csv`
- `MODEL_CANDIDATE_V1_REPAIRED_SOURCE_TIMING.csv`
- `MODEL_CANDIDATE_V1_REPAIRED_GUARDRAILS.md`
- `MODEL_CANDIDATE_V1_REPAIRED_README.md`
- `MODEL_CANDIDATE_V1_REPAIRED_REJECTION_LOG.md`

All outputs remain labeled:
`RESEARCH_CANDIDATE_ONLY`, `NOT_APPROVED`, `NOT_LATEST_CANDIDATE`,
`NOT_LATEST_APPROVED`, `NOT_PRIVATE_VALUE`, `NOT_RANKINGS`, `NOT_MOCK_DRAFT`,
and `NOT_FINAL_ADVICE`.

## Selected Safe Candidates

| Position | Candidate | Top-N | Years beating baseline | Worst drawdown | Status |
| --- | --- | ---: | ---: | ---: | --- |
| RB | `role_usage_core` | 0.500 | 3 | -0.042 | remains research candidate |
| WR | `safe_no_snap_no_depth_rank` | 0.528 | 2 | -0.028 | remains research candidate |

The repaired WR candidate has lower Top-N than the original blocked
`safe_no_snap` row, but still clears the research-candidate gate after removing
`depth_chart_best_rank`.

## Position Posture

| Position | Posture |
| --- | --- |
| QB | Baseline/control preferred; no V1 candidate package selected. |
| RB | `role_usage_core` remains local-only research candidate. |
| TE | `safe_baseline` remains preferred/reference. |
| WR | `safe_no_snap_no_depth_rank` remains local-only research candidate. |

## Vendor Appendix

The repaired package includes a local-only vendor appendix marker at:
`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622_repaired\vendor_research_appendix`

WR `vendor_rotowire_receiving_redzone` remains `VENDOR_RESEARCH_ONLY`,
`YELLOW_HOLD`, `NOT_SAFE_CANDIDATE`, and
`SOURCE_LICENSE_REVIEW_REQUIRED`. Vendor features are excluded from the repaired
safe candidate package and must not flow into private value, rankings, Mock
Draft, simulations, or final advice.

## Guardrail Summary

| Check | Result |
| --- | --- |
| `depth_chart_best_rank` removed | PASS |
| Rank-like depth-chart fields absent from safe package | PASS |
| Vendor fields absent from safe package | PASS |
| ADP/ECR/rank/projection/market/trade/private-value fields absent | PASS |
| `fantasy_points` / `fantasy_points_ppr` absent as input features | PASS |
| Source/timing rows present for each feature | PASS |
| Unknown timing absent | PASS |
| Blocked-field scan | PASS |
| Leakage scan | PASS |
| `latest_candidate` update | none |
| `latest_approved` update | none |

## Next Step

The repaired package is GREEN for a future model-readiness freeze decision. That
future decision must remain separate and explicit. This package is still
research-only and not final, approved, production, draft-ready, or promoted.

No raw local result tables, raw vendor rows, prediction dumps, or
`C:\NWR_SHARED_DATA` package contents are committed here.
