# NWR Player Compare Decision UX V2 - 2026-06-23

## Verdict

GREEN for Phase 1 implementation.

## Change Summary

Player Compare now starts with a decision-first summary instead of putting raw context tables directly under the player selector.

The summary includes:

- lean / recommendation
- confidence
- biggest risk
- comparison target
- why draft
- why pass / risk
- what would change the decision
- best fit by context
- model disagreement / human-review flags
- rank signal

Detailed context moved behind tabs:

- Dynasty / NWR Context
- Market Baseline / Display-Only
- Outcome / Horizon
- Age / Injury / Risk
- Raw Details / Diagnostics

## Guardrails

- No frozen board mutation.
- No `final_board_rank` change.
- No Dynasty Rank overwrite.
- No model/value/ranking logic change.
- Market/ADP context remains display-only.
- Missing values use `Not enough information`.

## Browser Acceptance Targets

Test pairs for final browser pass:

- Jameson Williams vs Brian Thomas Jr
- Zay Flowers vs a rookie
- Drake Maye vs a rookie/veteran if available

## Remaining Caveats

Player Compare still depends on existing data coverage. If injury/per-game/recovery data is missing, the Age / Injury / Risk tab shows only the supported risk/caveat fields rather than fabricating injury model outputs.
