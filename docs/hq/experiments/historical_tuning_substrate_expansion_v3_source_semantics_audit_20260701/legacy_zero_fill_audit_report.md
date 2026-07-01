# Legacy Zero-Fill Audit Report

## Verdict

V3 does not silently accept legacy missing-to-zero behavior. It separates the retained features into:

- Source-recorded or role-structural zeros, allowed as review-only after source comparison.
- Derived zeros, allowed as review-only when derived from reviewed components.
- Optional source missingness, null-fenced in V3.
- Unsupported or forbidden families, blocked from the canonical V3 substrate.

## Remaining Fence

The original Backtest V1 generator still ends with broad zero fill. V3 fences the known unsafe optional cases rather than claiming they are explicit zeros:

- `prior_offensive_snaps`
- `prior_offense_pct`
- `prior_receiving_air_yards`
- `prior_receiving_yards_after_catch`

No missing values were converted to zero in V3. The V3 parquet is review-only and not production-approved.
