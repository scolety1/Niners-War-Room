# Missingness Semantics V1

Missing values remain `Not enough information`.

## Derived Fields

- `touches = carries + receptions` only when both components are known.
- `opportunities = carries + targets` only when both components are known.
- If either component is null, the derived value remains null.

## Explicit Zero

A zero is preserved only when the source provides an explicit numeric zero. Missing source values are not converted to zero.

## Snap Counts

Missing `offensive_snaps` or `offense_pct` is not zero snaps, no role, inactive, or healthy. It is `Not enough information`.

## Red-Zone Sidecar

Sparse Sleeper red-zone keys are not zero when absent. `rz_att` remains blocked/ambiguous and is not normalized.
