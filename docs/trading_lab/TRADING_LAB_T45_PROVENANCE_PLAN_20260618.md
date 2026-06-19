# Trading Lab T45 Provenance Plan - 2026-06-18

## Goal

Make every displayed value explain whether it is a fixture, placeholder, future integration label, or missing.

## Source Helpers

- `SourceStatus`
- `ValueProvenance`
- `IntegrationStatus`
- Fixture demo labels.
- Missing-data labels.
- Future-integration labels.

## UI Labels

- Fixture demo value.
- Real NWR integration not wired.
- Public fantasy market source not wired.
- Manual review required.

## Guardrails

- No fixture value may claim to be real.
- No public value may overwrite NWR value.
- No real integrations are added.

## Validation

Tests confirm fixture/demo status, missing labels, future labels, and UI data status copy.
