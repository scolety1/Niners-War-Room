# Trading Lab Guardrail Traceability Matrix

Date: 2026-06-18

| guardrail | docs_that_mention_it | tests_that_enforce_it | validator_coverage | gap | safe_next_improvement |
| --- | --- | --- | --- | --- | --- |
| No real-money trading | Charter, release audit, closeouts | T5/T6/T7/T11 tests | Text rejection and future gate | No runtime trading path exists | Keep as permanent prohibition |
| No broker orders | Charter, language taxonomy, blocked gate | T5/T6/T11 tests | Execution/order phrase rejection | No order objects exist | Keep validating text only |
| No broker/API integration | Source policy, taxonomy, future gate | Source/T5/T6/T11 tests | Broker/API phrase rejection | No API client exists | Do not add clients |
| No credentials/secrets | Source policy, templates, import audit | Source/T5/T6/T11 tests | Secret field/value rejection | No secret scanning CLI added | Keep config validation in memory |
| No automated execution | Charter, lifecycle, future gate | T5/T6/T10/T11 tests | Auto-execute phrase rejection | No scheduler/executor exists | Keep manual review trigger wording |
| No investment advice | No-advice guide, taxonomy, closeouts | T5/T6/T7 tests | Advice phrase rejection | Rewrites can expand | Add safe rewrite library |
| No data ingestion/fetching | Source policy, future gate, import audit | T6/T11 tests | Data workflow phrase rejection/HOLD | No ingestion code exists | Require explicit phase approval |
| No backtesting implementation | Backtesting guardrails, future gate | T11 tests | Future request HOLD | No engine exists | Design specs only |
| No generated outputs | Import audit, future gate | T6/T11 tests | Generated-output phrase HOLD/REJECT | No writer exists | Keep artifacts untracked |
| No app/deployment/fantasy changes | Charter, import audit, handoff packet | T11 tests | Future gate rejects/holds drift | No app wiring exists | Keep lane isolated |

## Interpretation

Validator coverage means prohibited language is rejected or held in manual
paper/research artifacts. It does not imply any runtime execution system exists.
