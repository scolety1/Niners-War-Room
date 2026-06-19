# Trading Lab T7 Artifact Validator Plan

Date: 2026-06-18

## Purpose

T7 completes a minimal validation-only layer for manual Trading Lab artifacts.
The validators operate on in-memory fake/manual payloads only. They do not read
files, write files, fetch data, connect to APIs, place orders, run backtests,
wire the app, or create generated outputs.

## Artifacts Covered

- Source inventory
- Research intake
- Manual lifecycle
- Watchlist note
- Strategy note
- Risk journal
- Paper journal
- Manual review packet

## Validators Already Present

- `validate_source_metadata`
- `validate_research_config`
- `validate_watchlist_note`
- `validate_paper_journal_entry`
- `validate_artifact_text_fields`

## Validators Added

- `validate_manual_artifact_payload`
- `MANUAL_ARTIFACT_REQUIRED_FIELDS`

## Validators Skipped

Dedicated dataclass validators for research intake, strategy notes, risk
journals, lifecycle transitions, and manual review packets remain skipped until
separately approved. T7 uses generic required-field and prohibited-language
checks only.

## Prohibited Content Coverage

T7 preserves rejection coverage for:

- Advice language
- Broker/API and credential language
- Execution language
- Private account language
- Secret-like values
- Data-ingestion and generated-output language

## Boundary

No ingestion, no execution, no broker/API, no credentials, no app wiring, no
deployment, no generated artifacts, no private account data, and no investment
advice.
