# NWR Overnight Model Tune V1 Candidate Review - 2026-06-22

Status: GREEN for review-gate documentation only. No model is promoted.

This review evaluates the V1 expanded tune candidates for future local-only
candidate-package review. It does not approve private value, rankings, hidden
sort, Mock Draft behavior, simulations, final draft advice, deployment,
`latest_candidate`, or `latest_approved`.

## Inputs

Repo summary:
`docs/hq/parallel_lanes/NWR_OVERNIGHT_MODEL_TUNE_V1_EXPANDED_RESULTS_20260622.md`

Local-only review packet:
`C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v1_expanded_20260622\candidate_review_gate`

Required local-only outputs were created:

- `CANDIDATE_REVIEW_SUMMARY.md`
- `CANDIDATE_REVIEW_BY_POSITION.csv`
- `CANDIDATE_REVIEW_FEATURE_LISTS.csv`
- `CANDIDATE_REVIEW_YEARLY_STABILITY.csv`
- `CANDIDATE_REVIEW_DECISION_LOG.md`

## Guardrails

| Check | Result |
| --- | --- |
| Blocked-field scan | PASS |
| Leakage scan | PASS |
| Vendor safe-candidate labeling | blocked |
| Model/private-value/ranking/draft-use approval | not granted |
| `latest_candidate` / `latest_approved` | not created or updated |

## Candidate Verdicts

| Position | Reviewed path | Top-N | Years beating baseline | Worst drawdown | Verdict |
| --- | --- | ---: | ---: | ---: | --- |
| QB | `role_usage_core` | 0.417 | 0 | -0.167 | HOLD_CONTROL_PREFERRED |
| RB | `role_usage_core` | 0.500 | 3 | -0.042 | ADVANCE_LOCAL_ONLY_CANDIDATE_REVIEW |
| TE | `safe_baseline` | 0.500 | 0 | -0.083 | BASELINE_PREFERRED |
| WR | `safe_no_snap` | 0.556 | 2 | -0.028 | ADVANCE_LOCAL_ONLY_CANDIDATE_REVIEW |
| WR | `vendor_rotowire_receiving_redzone` | 0.556 | 3 | 0.000 | VENDOR_RESEARCH_CANDIDATE_ONLY |

## Position Posture

### QB

Recommended posture: keep baseline/control preferred. The best QB row was
`role_usage_core`, but it remained a yellow challenger/control result rather
than a safe candidate. It improved aggregate Top-N, but the stability gate
recorded zero seasons beating baseline and a major collapse flag. Do not build
a QB candidate package from this path yet.

### RB

Recommended posture: advance `role_usage_core` to local-only candidate-package
review. It improved Top-N versus baseline, beat baseline in three evaluation
seasons, avoided the one-lucky-year flag, avoided the major-collapse flag, and
uses interpretable role/usage features including snap fields.

### TE

Recommended posture: keep `safe_baseline` as the reference path. TE did not
produce a stronger non-baseline candidate in this review gate. No TE candidate
package is recommended from V1.

### WR Safe Path

Recommended posture: advance `safe_no_snap` to local-only candidate-package
review. It reached 0.556 Top-N, beat baseline in two seasons, had only a small
worst-year drawdown, avoided the one-lucky-year flag, avoided the major-collapse
flag, and does not rely on snap fields or vendor fields.

### WR Vendor Path

Recommended posture: keep `vendor_rotowire_receiving_redzone` as research-only.
It was the best overall WR row and showed stable year-level evidence, but it
uses isolated vendor red-zone fields. It may only be labeled
`VENDOR_RESEARCH_CANDIDATE` and requires source/license review before any future
model/backtest package use. It must not become a safe candidate, private-value
source, ranking source, Mock Draft source, simulation source, or final advice
source.

## Candidate-Package Recommendation

Build a future local-only candidate-package review for:

- RB `role_usage_core`
- WR `safe_no_snap`

Do not build candidate packages for:

- QB `role_usage_core`
- TE non-baseline alternatives from V1
- WR vendor-enhanced variants as safe packages

Vendor research may remain in a separate research folder only, pending
source/license review and explicit approval.

## Final Statement

This review gate is GREEN for documentation and future local-only candidate
review planning. It is not a promotion gate and does not approve any tuned model
for private value, rankings, Mock Draft, simulations, deployment, draft advice,
`latest_candidate`, or `latest_approved`.
