# Formula Gauntlet Missingness Policy Review

## Decision

Missingness handling is sufficient for review-only component signal tests on the existing partial panel, but not sufficient for position-scoped tournaments or full Formula Gauntlet.

## Evidence

- V2 historical tuning substrate: no new missing-to-zero conversion.
- V3 historical tuning substrate: null semantics preserved.
- Snap/offense null fences retained: `811` rows per snap field.
- Air-yard/YAC null fences retained: `663` rows per field.
- Rows with at least one optional source fence: `1,371`.
- NFLVerse source decision says missing snap count is not zero snaps or no-role.
- Missing opportunity is not zero opportunity unless explicit source zero exists.
- Missing weekly roster row is not inactive/off-roster by assumption.
- Partial replay coverage file labels coverage as source-column availability, not exact Model v4 receipt coverage.

## Sparse-History And Low-Games

The partial replay miss-pattern packet identified:

- Sparse-history rows: `1,453`, `26.3%`.
- Prior-production decline false positives: `572`, `10.4%`.
- Low-prior-opportunity breakout misses: `91`, `25.8%` of false negatives.
- RB role-change proxy false positives: `205`, `35.8%` of false positives.

These are not blockers for component signal tests, but they are blockers for tournament advancement rules until a Master HQ contract defines thresholds and stop conditions.

## Required Future Policy

Before any Formula Gauntlet tournament, define:

1. Field-level true zero vs unknown rules.
2. Position-specific missingness thresholds.
3. Sparse-history flag definition.
4. Low-games flag definition.
5. Rookie/second-year uncertainty flag definition.
6. Missing component receipt handling.
7. Exclusion rules for blocked or not-enough-information rows.
8. Reporting schema for missingness deltas versus PYF.

## Non-Promotion Boundary

Missingness flags can support review-only diagnostics. They are not formula weights, production penalties, hidden sorts, source-truth values, or model inputs unless a future source/model gate separately approves them.
