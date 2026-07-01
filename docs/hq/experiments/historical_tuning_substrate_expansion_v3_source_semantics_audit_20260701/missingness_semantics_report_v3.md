# Missingness Semantics Report V3

V3 preserves null semantics. Missing values were not forced to zero.

## Null Fences Kept

- Snap/offense source missingness: `811` nulls retained per snap field.
- Air-yard/YAC source missingness: `663` nulls retained per field.
- Rows with at least one optional source fence: `1,371`.

Core seasonal stats remain non-null because they are source-recorded player-season stats in the emitted Backtest rows. They remain review-only, not model-approved source truth.
