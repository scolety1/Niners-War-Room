# Trading Lab Validator Inventory

Date: 2026-06-18

## Purpose

This inventory maps Trading Lab artifacts to current docs, tests, validators,
coverage, gaps, and safe next improvements. It does not approve data ingestion,
backtesting implementation, broker/API integration, deployment, generated
outputs, or investment advice.

| artifact_type | relevant_docs_contracts | existing_tests | validators_helpers | prohibited_language_coverage | secret_like_value_coverage | broker_api_execution_rejection | remaining_gap | safe_next_improvement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| source inventory | Source policy, source template, source schema examples, blocked-work gate | `test_trading_lab_source_inventory.py`, T3/T4/T5 tests | `ResearchSourceMetadata`, `validate_source_metadata`, `validate_research_config` | Category/use checks plus text checks | Config fields and values | Broker/API/execution text rejected | No persisted manifest approved | Docs-only manifest acceptance criteria |
| research intake | Research intake template and schema contract | T5/T6 text tests | `validate_artifact_text_fields` | Advice, broker, private account, execution, data workflow | Secret-like values | Broker/credential/execution text rejected | No intake dataclass | Optional validation-only dataclass later |
| manual lifecycle | Lifecycle guide and schema contract | T5/T6 text tests | `validate_artifact_text_fields` | Invalid transition language | Secret-like values | Broker/credential/execution text rejected | No state machine approved | Keep docs-only unless explicitly approved |
| watchlist note | Watchlist templates, examples, schema v2 | `test_trading_lab_watchlist_contract.py`, T3/T4/T5 tests | `WatchlistNote`, `validate_watchlist_note`, `validate_artifact_text_fields` | Paper-only/source/execution checks plus text checks | Secret-like values via text helper | Execution and broker/credential text rejected | Schema v2 fields not fully dataclass-backed | Optional v2 validator later |
| strategy note | Strategy template and schema v2 | T5/T6 text tests | `validate_artifact_text_fields` | Advice, execution, broker, private data, data workflow | Secret-like values | Broker/credential/execution text rejected | No dedicated strategy dataclass | Optional validation-only helper later |
| risk journal | Risk template and schema v2 | T5/T6 text tests | `validate_artifact_text_fields` | Private data, advice, execution, broker, data workflow | Secret-like values | Broker/credential/execution text rejected | No dedicated risk dataclass | Optional validation-only helper later |
| paper journal | Paper template, expectations, schema v2 | `test_trading_lab_paper_journal_contract.py`, T3/T5 tests | `PaperJournalEntry`, `validate_paper_journal_entry`, `validate_artifact_text_fields` | Execution/private-account/secret text checks | Secret-like values | Execution text rejected | Review statuses documented but not enforced | Optional status constants later |
| manual review packet | Manual review packet template and examples | T6 text tests | `validate_artifact_text_fields` | Advice, execution, private data, broker, data workflow | Secret-like values | Broker/credential/execution text rejected | No packet dataclass | Keep docs-only until approved |
| blocked-work gates | Blocked-work gate and future phase gate | T6 text tests | `validate_artifact_text_fields` | Data-ingestion/generated-output terms rejected in artifact text | Secret-like values | Broker/credential/execution text rejected | Gate remains manual | Require explicit user approval for proposals |
