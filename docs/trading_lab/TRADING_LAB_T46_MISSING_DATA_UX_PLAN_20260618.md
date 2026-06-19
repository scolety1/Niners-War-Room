# Trading Lab T46 Missing Data UX Plan - 2026-06-18

## Goal

Make Trade Lab graceful when future integrations are unavailable or incomplete.

## Missing States

- Missing NWR value.
- Missing public fantasy market value.
- Missing roster context.
- Missing drop pressure.
- Missing rookie/mock context.
- Missing opponent context.
- No packages available.
- Unsupported mode fallback.
- All assets excluded.

## Guardrails

- Missing data must not claim a real integration exists.
- Missing public market value must not break scoring review.
- Fallbacks remain fixture-only.
- No generated outputs.

## Validation

Tests cover placeholder labels, safe public-market fallback, no-package fallback, unsupported mode fallback, and no real integration claims.
