# Formula Search Plateau Decision

## Decision

`FORMULA_SEARCH_PLATEAU_CONFIRMED_WITH_CURRENT_INGREDIENTS`

## Findings

- Refinement did not improve over the prior Gauntlet best: `0.755` versus `0.755`.
- All `136` refinement candidates beat PYF, which confirms the current production-weight neighborhood is better than the anchor baseline.
- `0` candidates beat the prior Gauntlet best.
- `0` seed neighborhoods materially improved over seed references.
- Top candidates are not materially different signals; they are variants of the same multi-year production family with small age/lifecycle, role, and decline-context changes.

## Decision

Pause further same-ingredient refinement. Preserve the current best review-only references, but do not run another formula sweep until a data upgrade adds a genuinely new allowed input or improves the data substrate.
