# Trading Lab Doc Traceability Matrix

Date: 2026-06-18

| doc_name | purpose | artifact_type | related_validator_test | related_guardrail | status | next_safe_maintenance |
| --- | --- | --- | --- | --- | --- | --- |
| `TRADING_LAB_CHARTER_20260618.md` | Lane purpose and prohibitions | lane charter | Docs-only | No execution, no advice, no fantasy changes | Ready | Keep aligned with future closeouts |
| `TRADING_LAB_SOURCE_AND_DATA_POLICY_20260618.md` | Source/data rules | source inventory | `validate_source_metadata` | No secrets, no private account data | Ready | Add docs-only source review examples |
| `TRADING_LAB_SOURCE_INVENTORY_TEMPLATE_20260618.md` | Source review template | source inventory | Source inventory tests | Public/manual sources only | Ready | Keep fake examples public-only |
| `TRADING_LAB_RESEARCH_INTAKE_SCHEMA_CONTRACT_20260618.md` | Intake fields and statuses | research intake | T5/T6/T7 tests | Paper-only, no advice | Ready | Optional validation-only dataclass later |
| `TRADING_LAB_MANUAL_LIFECYCLE_SCHEMA_CONTRACT_20260618.md` | Manual states and transitions | manual lifecycle | T10 tests | No execution state | Ready | Keep manual-only |
| `TRADING_LAB_WATCHLIST_NOTE_SCHEMA_V2_20260618.md` | Watchlist schema v2 | watchlist note | Watchlist tests | Paper-only, public sources | Ready | Optional v2 helper later |
| `TRADING_LAB_STRATEGY_NOTE_SCHEMA_V2_20260618.md` | Strategy note expectations | strategy note | T5/T6/T7 tests | Not investment advice | Ready | Add examples only |
| `TRADING_LAB_RISK_JOURNAL_SCHEMA_V2_20260618.md` | Risk categories and scales | risk journal | T5/T6/T7 tests | Risk framing, no execution | Ready | Optional status constants |
| `TRADING_LAB_PAPER_JOURNAL_SCHEMA_V2_20260618.md` | Paper journal fields | paper journal | Paper journal tests | No real orders | Ready | Optional review status constants |
| `TRADING_LAB_MANUAL_REVIEW_PACKET_TEMPLATE_20260618.md` | End-to-end manual packet | manual review packet | T9 tests | Manual review only | Ready | Keep packet in-memory/manual |
| `TRADING_LAB_FUTURE_PHASE_DECISION_GATE_20260618.md` | Future phase preconditions | blocked-work gate | T11 tests | HOLD/REJECT future work | Ready | Require explicit approval |
| `TRADING_LAB_T12_RELEASE_CANDIDATE_AUDIT_20260618.md` | Release readiness | release audit | Full focused tests | Confirms blocked areas | Ready | Refresh at freeze points |

## Notes

This matrix is a maintenance aid. It does not approve implementation of data
ingestion, simulation, backtesting, broker/API, deployment, or app wiring.
