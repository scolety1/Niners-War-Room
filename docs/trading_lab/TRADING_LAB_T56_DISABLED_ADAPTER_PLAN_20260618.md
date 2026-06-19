# Trading Lab T56 Disabled Adapter Plan - 2026-06-18

## Goal

Make future integrations explicit but disabled so the UI can safely show unavailable states.

## Providers

- `DisabledNwrValueProvider`
- `DisabledPublicMarketProvider`
- `DisabledRosterContextProvider`
- `DisabledRookieMockContextProvider`

## Guardrails

- No real data loading.
- No imports from other lanes.
- No file paths.
- No APIs.
- No generated outputs.

## Validation

Tests confirm disabled providers return not-wired status, do not return fixture values, do not expose file/API methods, and can be represented in UI labels.
