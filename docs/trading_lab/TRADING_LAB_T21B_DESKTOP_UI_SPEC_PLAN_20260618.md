# Trading Lab T21B Desktop UI Spec Plan

Date: 2026-06-18

## Purpose

T21B defines the corrected desktop-first Trade Lab UI after the Wall Street
cleanup. The UI is for fantasy football trade value work only.

## Corrected Product Direction

Trading Lab helps identify realistic fantasy football trades where public
fantasy market value makes the deal acceptable, but NWR private value says the
move improves our roster.

## Work Planned

- Define the desktop-first three-column layout.
- Define the supported trade modes.
- Define the best trade card, package ranking, negotiation ladder, bad trade
  detector, and roster aftermath panels.
- Define data status placeholders and future scope.
- Preserve explicit non-goals.

## Guardrails

- No app route wiring in T21B.
- No data ingestion.
- No real fantasy source integration.
- No generated outputs.
- No Wall Street or finance product framing.

## Validation Plan

Run `git diff --check`, inspect docs diff, and keep changed files inside
`docs/trading_lab/`.
