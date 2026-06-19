# Trading Lab T16 Fake Example Expansion Plan

Date: 2026-06-18

## Purpose

T16 expands fake Trading Lab examples and locks them with regression tests. The
examples are inline, fictional, and paper/research-only.

## Scope

- Add valid fake examples for supported artifact types.
- Add invalid fake examples for supported artifact types.
- Add HOLD examples for ambiguous future-phase work.
- Add regression tests using inline fake payloads only.

## Supported Artifact Types

- source inventory
- research intake
- manual lifecycle
- watchlist note
- strategy note
- risk journal
- paper journal
- manual review packet
- blocked-work gate

## Fake Symbol Rule

Use only fake symbols such as `EXMPL`, `PAPER`, `SIM`, `REVIEW`, and `FAKE`.

## Guardrails

No JSON, CSV, market datasets, data files, generated outputs, ingestion,
fetching, broker/API integration, execution, simulation engine, app wiring, or
deployment are allowed.
