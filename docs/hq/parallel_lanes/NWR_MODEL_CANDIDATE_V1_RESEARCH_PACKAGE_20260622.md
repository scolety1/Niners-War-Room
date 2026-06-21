# NWR Model Candidate V1 Research Package - 2026-06-22

Status: GREEN for local-only research package creation. No model is approved.

This document records the local-only Model Candidate V1 research package created
from the GREEN Overnight Model Tune V1 Candidate Review Gate. It does not
approve private value, rankings, hidden sort, Mock Draft behavior, simulations,
final draft advice, deployment, `latest_candidate`, or `latest_approved`.

## Local-Only Package

Package root:
`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622`

Required local-only files created:

- `MODEL_CANDIDATE_V1_MANIFEST.csv`
- `MODEL_CANDIDATE_V1_BY_POSITION.csv`
- `MODEL_CANDIDATE_V1_FEATURES.csv`
- `MODEL_CANDIDATE_V1_METRICS.csv`
- `MODEL_CANDIDATE_V1_YEARLY_STABILITY.csv`
- `MODEL_CANDIDATE_V1_SOURCE_TIMING.csv`
- `MODEL_CANDIDATE_V1_GUARDRAILS.md`
- `MODEL_CANDIDATE_V1_README.md`
- `MODEL_CANDIDATE_V1_REJECTION_LOG.md`

All package outputs are labeled:
`RESEARCH_CANDIDATE_ONLY`, `NOT_APPROVED`, `NOT_LATEST_CANDIDATE`,
`NOT_LATEST_APPROVED`, `NOT_PRIVATE_VALUE`, `NOT_RANKINGS`, `NOT_MOCK_DRAFT`,
and `NOT_FINAL_ADVICE`.

## Selected Safe Candidates

| Position | Candidate | Feature family | Model | Top-N | Years beating baseline | Worst drawdown | Spearman | MAE | RMSE |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RB | `role_usage_core` | YELLOW_CHALLENGER | extra trees | 0.500 | 3 | -0.042 | 0.676 | 42.672 | 57.481 |
| WR | `safe_no_snap` | SAFE_NO_SNAP | extra trees | 0.556 | 2 | -0.028 | 0.714 | 30.471 | 39.490 |

The RB candidate uses role/usage signals including snap fields. The WR safe
candidate intentionally uses the no-snap path and contains no vendor fields.

## Position Posture

| Position | Posture |
| --- | --- |
| QB | Baseline/control preferred; no V1 candidate package selected. |
| RB | `role_usage_core` advances as local-only research candidate. |
| TE | `safe_baseline` remains preferred/reference. |
| WR | `safe_no_snap` advances as local-only research candidate. |

## Hold And Rejected Paths

| Path | Status | Reason |
| --- | --- | --- |
| QB `role_usage_core` | HOLD_CONTROL_PREFERRED | Aggregate Top-N improved, but the stability gate recorded zero seasons beating baseline and a major collapse flag. |
| TE non-baseline alternatives | BASELINE_PREFERRED | No reviewed V1 path beat the baseline/reference posture safely enough. |
| WR `vendor_rotowire_receiving_redzone` | VENDOR_RESEARCH_ONLY | Strong research signal, but vendor fields require source/license review and cannot be safe candidates. |

## Vendor Appendix

A quarantined local-only vendor appendix was created at:
`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622\vendor_research_appendix`

The appendix summarizes WR `vendor_rotowire_receiving_redzone` as
`VENDOR_RESEARCH_ONLY`, `YELLOW_HOLD`, `NOT_SAFE_CANDIDATE`, and
`SOURCE_LICENSE_REVIEW_REQUIRED`. Vendor features were not mixed into the safe
candidate package and must not flow into private value, rankings, Mock Draft,
simulations, or final advice.

## Guardrail Results

| Check | Result |
| --- | --- |
| Blocked-field scan | PASS |
| Leakage scan | PASS |
| Vendor fields in safe candidate package | none |
| `latest_candidate` update | none |
| `latest_approved` update | none |
| Private value / rankings / Mock Draft / simulations | not touched |

## Next Step

Recommended next step: perform a future local-only candidate-package review for
RB `role_usage_core` and WR `safe_no_snap`. This should remain research-only
until Tim/Master explicitly approves a separate promotion path.

No raw local result tables, raw vendor rows, prediction dumps, or
`C:\NWR_SHARED_DATA` package contents are committed here.
