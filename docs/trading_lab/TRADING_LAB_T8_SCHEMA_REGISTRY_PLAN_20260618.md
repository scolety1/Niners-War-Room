# Trading Lab T8 Schema Registry Plan

Date: 2026-06-18

T8 centralizes manual schema knowledge for Trading Lab artifacts without adding
file I/O, data ingestion, generated outputs, app wiring, broker/API work, or
execution.

Scope:

- Docs-only schema registry
- Constants-only schema registry in `src/trading_lab/`
- Fake inline example corpus
- Focused tests for registry completeness and prohibited field names

Boundary:

- No JSON, CSV, data files, generated artifacts, external schema dependencies,
  market-data fetches, broker/API integrations, credentials, or real account
  data
