# Trading Lab Validation Coverage Matrix

Date: 2026-06-18

## Purpose

This matrix maps Trading Lab artifacts to current docs-only and validation-only
coverage. It does not open data ingestion, backtesting implementation,
broker/API integration, deployment, app wiring, or investment advice.

| artifact | doc/template | validator/test coverage | prohibited content covered | current status | gap | safe next improvement |
| --- | --- | --- | --- | --- | --- | --- |
| Source inventory | Source inventory template, validation examples, T6 validator inventory, T7 coverage, T8 schema registry | `validate_source_metadata`, `validate_research_config`, schema registry, T3/T4/T5/T6/T7/T8 tests | Prohibited categories, broker/API language, secret-like config fields, prohibited field names | Ready for manual review | No persisted manifest approved | Docs-only manifest acceptance criteria |
| Watchlist notes | Watchlist template, examples, schema v2, T7 coverage | `validate_watchlist_note`, `validate_artifact_text_fields`, `validate_manual_artifact_payload`, watchlist/T3/T4/T5/T6/T7 tests | Paper-only flag, public sources, execution/advice/broker/private-data language | Ready for paper notes | Schema v2 fields not fully dataclass-backed | Optional v2 validator later |
| Paper journal | Paper journal template, expectations, schema v2, T7 coverage | `validate_paper_journal_entry`, `validate_artifact_text_fields`, `validate_manual_artifact_payload`, paper journal/T3/T5/T6/T7 tests | Execution language, private account language, secret-like values, advice/data workflow text | Ready for manual paper entries | Review statuses documented but not enforced | Optional status constants later |
| Risk journal | Risk journal template, expectations, schema v2, T7 coverage | `validate_artifact_text_fields`, `validate_manual_artifact_payload`, T5/T6/T7 tests | Advice drift, execution-policy risk, private data risk, data workflow text | Ready for manual review | No dedicated risk dataclass | Optional future validation-only helper |
| Strategy notes | Strategy template, expectations, schema v2, T7 coverage | `validate_artifact_text_fields`, `validate_manual_artifact_payload`, T5/T6/T7 tests | Buy/sell language, broker/order language, automated triggers, secret text | Ready for manual review | No dedicated strategy dataclass | Optional future validation-only helper |
| Backtesting readiness | Guardrails, readiness checklist, blocked-work gate, future phase gate | Docs-only coverage plus T6 data-workflow text tests | No code, no ingestion, no broker/API, bias warnings, generated-output blocks | HOLD before implementation | Implementation not approved | Separate explicit phase gate |
| Research intake | Research intake template and schema contract | `validate_artifact_text_fields`, T5/T6 tests | Credentials, private account references, broker/API dependency, advice/data workflow text | Ready for manual intake | No intake dataclass | Optional intake validation-only helper |
| Manual lifecycle | Manual lifecycle guide, schema contract, T10 expectations | `is_valid_lifecycle_transition`, `validate_lifecycle_transition`, T5/T6/T10 tests | Invalid transitions to orders, credentials, auto-execution, private data, data workflow text | Ready for manual operation | No execution state machine, by design | Keep in-memory/manual only |
| Manual review packet | Manual review packet template, examples, T9 plan and expectations | `validate_manual_review_packet`, `validate_artifact_text_fields`, T6/T9 tests | Missing sections, advice, execution, private-account, broker, credential, data workflow text | Ready for manual review | No packet dataclass | Keep in-memory unless approved |
| Blocked-work gates | Blocked-work gate, future phase gate, T11 plan and expectations | `classify_future_phase_request`, `validate_future_phase_request`, T6/T11 tests | Data ingestion, generated outputs, broker/API, credentials, execution, advice, private account data, deployment, fantasy-lane drift | Ready for proposal screening | No future phase approved | Require explicit user approval |
| Schema registry | T8 schema registry and fake corpus | `SCHEMA_REGISTRY`, `schema_for_artifact`, T8 tests | Prohibited field names and artifact coverage | Ready for docs/tests | Constants only, no file format | Keep examples inline unless approved |
| Release readiness | T12 audit, Master handoff packet, next phase options, chain closeout | Docs-only audit plus full focused Trading Lab validation before commit | Confirms no execution, broker/API, credentials, data ingestion, generated outputs, deployment, or fantasy-lane work | Ready for Master review after clean push | T12 commit hash recorded in final report | Keep future phases behind explicit approval |
| Docs traceability | T14 plan, doc traceability matrix, guardrail traceability matrix, style guide | Docs-only; full focused Trading Lab validation before commit | Maps no-advice, no-execution, no data ingestion, no deployment, no fantasy drift | Ready for maintenance | Traceability is additive, not enforcement by itself | Refresh when new docs/tests are added |
| Validator edge cases | T15 edge-case plan and closeout | `test_trading_lab_t15_validator_edge_cases.py` | Mixed case, punctuation-separated terms, nested payload text, nested config strings, missing fields, unsupported artifact type, ambiguous future work | Ready for validation-only use | No file/schema parser approved | Keep edge cases inline and fake |
| Fake example corpus | T16 plan, fake corpus v2, closeout | `test_trading_lab_t16_fake_example_regressions.py` | ACCEPT/REJECT/HOLD examples across source, intake, lifecycle, watchlist, strategy, risk, paper journal, packet, and blocked gate | Ready for regression use | Inline only, no external corpus file | Keep examples fictional and public-only |
| No-advice language lock | T17 plan, safe rewrite library, prohibited language taxonomy | `test_trading_lab_t17_no_advice_rewrites.py` | Buy/sell/order, broker token, API key, private balance, auto-execute, guaranteed-return language | Ready for language hygiene | Rewrite library is docs guidance, not advice | Keep rewrites as questions/risks/manual review |
| Source policy gates | T18 source policy plan, license review template, decision tree | `test_trading_lab_t18_source_policy_gates.py` | Public source accepted, unclear license held, private brokerage/credential rejected, paid/private dump held | Ready for manual source review | Not legal advice; no downloads approved | Keep as source review gate only |
| Simulation design gates | T19 design spec, blockers, not-implemented assertion | Docs-only; existing T11 blocked-work tests cover proposal HOLD/REJECT behavior | No ingestion, no fetching, no generated outputs, no broker/API, no execution, no implementation | HOLD before implementation | Design spec does not approve code | Require explicit user/Master approval |

## Coverage Notes

- Docs-only coverage is intentional for operator workflow and readiness.
- Code/test coverage remains isolated to Trading Lab validators.
- Remaining gaps do not block manual paper/research operation.
- Remaining gaps do block automation, ingestion, backtesting implementation, and
  execution workflows.
