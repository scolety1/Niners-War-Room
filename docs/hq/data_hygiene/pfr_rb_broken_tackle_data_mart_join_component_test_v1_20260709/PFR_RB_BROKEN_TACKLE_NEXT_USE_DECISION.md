# PFR RB Broken Tackle Next Use Decision

## Decision

`AVAILABLE_BUT_NO_INCREMENTAL_SIGNAL`

## Maximum Allowed Use

Review-only evidence/slice context only. The current component result does not justify another PFR-specific formula branch. The sidecar should remain preserved as evidence, but it may not be used as production model input, direct ranking input, hidden sort logic, or broad PFR source promotion.

## Recommended Next Lane

`Historical Market / ADP Source Gate and Data Mart Join V1`

## Rationale

The PFR branch now has actual values, a review-only sidecar, source hash validation, lagged as-of handling, and RB-only component metrics. The evidence is not strong enough for a PFR-specific follow-up: raw and per-game broken-tackle values trail PYF and multi-year production, and `per_attempt` is weak diagnostic-only. The larger accuracy path should pivot to market/ADP source-gate work.
