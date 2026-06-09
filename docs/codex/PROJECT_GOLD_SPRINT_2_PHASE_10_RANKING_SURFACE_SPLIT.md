# Project Gold Sprint 2 / Phase 10: Ranking Surface Split

Date: 2026-05-14

## Goal

Stop one composite board from pretending to answer every question.

## Completed

- Added an explicit ranking-surface contract in `src/services/ranking_surface_service.py`.
- Defined five review-only surfaces:
  - Pure Model Value
  - Keeper Decision
  - Trade/Liquidity
  - Forced-Release Pain
  - Draft Board / Available Players Only
- Updated War Board to use surface-specific ranking sources, intended-use text, sorting, and display columns.
- Updated Rankings and Draft Board to declare the draft-available rank source.
- Updated ranking audit rows so War Board exposes each surface separately.
- Added regression tests for:
  - surface metadata
  - pure model value excluding keeper/market/rule context
  - keeper decision using roster/action context
  - trade/liquidity using market disagreement
  - forced-release pain filtering to team top-five candidates
  - draft available filtering out drafted players

## Safety Notes

- No player formulas were changed.
- No readiness gates were unlocked.
- Rankings remain review-only.

## Verification

Focused tests passed:

```text
30 passed
```

Full static check passed:

```text
645 passed
Niners War Room static check passed.
```
