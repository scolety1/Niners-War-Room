# One-year result

No genuinely untouched, leakage-safe, outcome-complete 1Y cohort was admitted.

The immutable raw-snapshot audit found:

- 2024 rookies: 66 recorded target-season rows of 77; 11 absent.
- 2025 rookies: 70 of 85; 15 absent.
- 2024 veteran states: 446 of 586; 140 absent.
- 2025 veteran states: 458 of 596; 138 absent.

The recovered builder used `sum(value is not None for value in yearly)` over constructed calendar slots and set points to zero when a target stats row was absent. Therefore its nominal `followup_seasons_observed` is not evidence of observed outcomes.

Result: **blocked for production validation**. The product still answers 2026 win-now through the separately admitted Redraft authority; that is a current-season projection, not a validated dynasty 1Y common value.
