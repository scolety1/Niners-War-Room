# Trading Lab Validation Coverage Matrix

Date: 2026-06-18

## Purpose

This matrix maps Trading Lab artifacts to current docs-only and validation-only
coverage. It does not open data ingestion, backtesting implementation,
broker/API integration, deployment, app wiring, or investment advice.

| artifact | doc/template | validator/test coverage | prohibited content covered | current status | gap | safe next improvement |
| --- | --- | --- | --- | --- | --- | --- |
| Source inventory | Source inventory template and validation examples | `validate_source_metadata`, T3 source tests | Prohibited categories, broker/API language, secret-like config fields | Ready for manual review | No persisted manifest approved | Docs-only manifest acceptance criteria |
| Watchlist notes | Watchlist template and examples | `validate_watchlist_note`, watchlist tests | Paper-only flag, public sources, execution language | Ready for paper notes | No lifecycle linkage validator | Docs-only lifecycle acceptance examples |
| Paper journal | Paper journal template and validation expectations | `validate_paper_journal_entry`, paper journal tests | Execution language, private account language, secret-like values | Ready for manual paper entries | No persisted journal file approved | Docs-only journal closeout examples |
| Risk journal | Risk journal template and expectations | Docs-only coverage | Advice drift, execution-policy risk, private data risk | Ready for manual review | No code validator | Optional future validation-only helper |
| Strategy notes | Strategy note template and expectations | Docs-only coverage | Buy/sell language, broker/order language, automated triggers | Ready for manual review | No code validator | Optional future validation-only helper |
| Backtesting readiness | Guardrails and readiness checklist | Docs-only coverage | No code, no ingestion, no broker/API, bias warnings | HOLD before implementation | Implementation not approved | Separate explicit phase gate |
| Research intake | Research intake template | Docs-only coverage | Credentials, private account references, broker/API dependency | Ready for manual intake | No code validator | Optional intake validation-only tests |
| Manual lifecycle | Manual lifecycle guide | Docs-only coverage | Invalid transitions to orders, credentials, auto-execution | Ready for manual operation | No state machine code approved | Keep as docs-only unless approved |

## Coverage Notes

- Docs-only coverage is intentional for operator workflow and readiness.
- Code/test coverage remains isolated to Trading Lab validators.
- Remaining gaps do not block manual paper/research operation.
- Remaining gaps do block automation, ingestion, backtesting implementation, and
  execution workflows.
