# Trading Lab T43 Integration Seam Plan - 2026-06-18

## Goal

Document how future real NWR integrations should attach to Trade Lab without touching other lanes now.

## Current State

Trade Lab is fixture-only. It has contracts, fixture providers, scoring, package builders, negotiation helpers, roster aftermath helpers, warning helpers, and an isolated Streamlit page.

## Future Seam Rules

- Future integrations must be read-only unless a later explicit approval says otherwise.
- Each integration must attach through an adapter contract inside `src/trading_lab/`.
- NWR private value must remain separate from public fantasy market value.
- Public fantasy source values must never overwrite NWR private value.
- Missing data must render as a clear placeholder.
- No future integration may create generated outputs without explicit approval.

## No-Go Areas

- No imports from Outcome, Rookie, Mock Draft, Drop Decision, Deployment V2, or Master now.
- No app shell wiring changes.
- No public fantasy source API work.
- No data ingestion.
- No automated trade submission.
- No league transaction execution.

## Validation Plan

- Docs-only diff check.
- Confirm only `docs/trading_lab/` files are staged.
