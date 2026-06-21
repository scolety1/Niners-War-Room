# NWR Model Candidate V1 QA Gate - 2026-06-22

Status: RED for model-freeze readiness. No model is approved.

This QA gate audited the local-only Model Candidate V1 research package before
any model-readiness freeze decision. It does not approve private value,
rankings, hidden sort, Mock Draft behavior, simulations, final draft advice,
deployment, `latest_candidate`, or `latest_approved`.

## Local-Only QA Path

`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622\qa_gate`

Required local-only QA files were created:

- `MODEL_CANDIDATE_V1_QA_SUMMARY.md`
- `MODEL_CANDIDATE_V1_QA_CHECKLIST.csv`
- `MODEL_CANDIDATE_V1_QA_FEATURE_AUDIT.csv`
- `MODEL_CANDIDATE_V1_QA_TIMING_AUDIT.csv`
- `MODEL_CANDIDATE_V1_QA_VENDOR_SEPARATION_AUDIT.csv`
- `MODEL_CANDIDATE_V1_QA_DECISION_LOG.md`

## QA Verdict

| Area | Result |
| --- | --- |
| Package exists and required files present | PASS |
| Required NOT-approved labels present | PASS |
| Selected candidates match review gate | PASS |
| QB / TE not promoted | PASS |
| Vendor candidate quarantined | PASS |
| Vendor fields absent from safe package | PASS |
| Blocked / market / rank field feature audit | FAIL |
| Fantasy points absent from input features | PASS |
| Source/timing rows present for all safe features | PASS |
| Unknown timing absent | PASS |
| Metrics match review gate and V1 expanded tune | PASS |
| Yearly stability evidence present | PASS |
| Drawdown and collapse flags recorded | PASS |
| Blocked-field scan included and PASS | PASS |
| Leakage scan included and PASS | PASS |
| No approval claims | PASS |

Final QA verdict: RED.

## Blocker

The WR `safe_no_snap` candidate package includes `depth_chart_best_rank` in the
safe feature list. The QA gate treats this as a rank-like field under the
candidate-package policy. Because rank fields are blocked as model inputs, the
package is not ready for a model-freeze decision.

This does not mean the V1 research run or candidate review was invalid. It means
the candidate package needs repair or explicit policy review before any freeze
decision.

## Selected Candidates Verified

| Position | Candidate | QA status |
| --- | --- | --- |
| RB | `role_usage_core` | Verified as research-only candidate. |
| WR | `safe_no_snap` | Blocked by `depth_chart_best_rank` feature audit issue. |

## Position Posture Verified

| Position | Posture |
| --- | --- |
| QB | Baseline/control preferred; not promoted. |
| RB | Research candidate only; not approved. |
| TE | Baseline/reference preferred; not promoted. |
| WR | Research candidate only, but freeze readiness is blocked pending feature repair/review. |

## Timing Audit

Source/timing classes exist for every safe feature and no unknown-timing fields
were found. Historical feature-season timing is acceptable for this local-only
research package, but it remains a warning for any future live-use posture. This
QA gate does not approve live use.

## Vendor Separation

Vendor separation passed. The WR `vendor_rotowire_receiving_redzone` path remains
quarantined in the local-only vendor appendix as `VENDOR_RESEARCH_ONLY`,
`YELLOW_HOLD`, `NOT_SAFE_CANDIDATE`, and
`SOURCE_LICENSE_REVIEW_REQUIRED`. Vendor fields were not mixed into the safe
candidate metrics or safe feature list.

## Guardrails

| Check | Result |
| --- | --- |
| Leakage scan | PASS |
| Existing V1 blocked-field scan | PASS |
| QA safe feature rank-field audit | FAIL |
| `latest_candidate` update | none |
| `latest_approved` update | none |
| Private value / rankings / Mock Draft / simulations | not touched |

## Readiness For Next Freeze Decision

RED. Do not proceed to a model-readiness freeze until the
`depth_chart_best_rank` issue is repaired or resolved by explicit source-policy
review. A future repair should keep the package local-only, rerun this QA gate,
and continue to exclude vendor fields from safe candidates.

No raw local result tables, raw vendor rows, prediction dumps, or
`C:\NWR_SHARED_DATA` package contents are committed here.
