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
| Manual lifecycle | Manual lifecycle guide and schema contract | `validate_artifact_text_fields`, T5/T6 tests | Invalid transitions to orders, credentials, auto-execution, data workflow text | Ready for manual operation | No state machine code approved | Keep as docs-only unless approved |
| Manual review packet | Manual review packet template and examples | `validate_artifact_text_fields`, T6 tests | Advice, execution, private-account, broker, credential, data workflow text | Ready for manual review | No packet dataclass | Keep docs-only unless approved |
| Blocked-work gates | Blocked-work gate, future phase gate | Docs-only coverage plus T6 text tests | Data ingestion, generated outputs, broker/API, credentials, execution, advice | Ready for proposal screening | No future phase approved | Require explicit user approval |
| Schema registry | T8 schema registry and fake corpus | `SCHEMA_REGISTRY`, `schema_for_artifact`, T8 tests | Prohibited field names and artifact coverage | Ready for docs/tests | Constants only, no file format | Keep examples inline unless approved |

## Coverage Notes

- Docs-only coverage is intentional for operator workflow and readiness.
- Code/test coverage remains isolated to Trading Lab validators.
- Remaining gaps do not block manual paper/research operation.
- Remaining gaps do block automation, ingestion, backtesting implementation, and
  execution workflows.
