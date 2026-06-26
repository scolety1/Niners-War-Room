# NFL Usage Backtest Target Label Audit

## Verdict

YELLOW_LIMITED_TARGETS_AVAILABLE.

Approved future outcome labels exist with conditions, but the promotion gate does not have a committed multi-season usage feature panel. Predictive usage-field promotion is blocked until that coverage exists.

## Conditionally Approved Targets

- `next_nwr_points`
- `next_nwr_ppg`
- `position_finish_flags`

## Blocked Targets

- `outcome_columns_display_props`
- `market_adp_dynastyprocess_projection_values`

## Backtest Recommendation

Run coverage, leakage, and display-context diagnostics now. Do not run predictive promotion or claim model-candidate status until the historical usage panel and target manifest are available.
