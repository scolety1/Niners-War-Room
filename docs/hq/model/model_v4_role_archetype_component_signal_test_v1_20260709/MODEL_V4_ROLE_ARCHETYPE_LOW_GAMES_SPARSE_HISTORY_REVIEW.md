# Model v4 Role Archetype Low-Games / Sparse-History Review

## Summary

- Sparse-history rows: `1453`
- Sparse-history position distribution: `{'QB': 328, 'RB': 344, 'TE': 342, 'WR': 439}`
- Sparse-history startable hits: `48`
- Sparse-history startable rate: `3.3%`
- Sparse-history PYF false negatives: `48`

## Finding

The sparse-history archetypes are useful review-only guardrails. They identify a large unstable slice, but they must not be treated as automatic fades because some sparse-history players do become startable.

## Caveat

Sparse-history is a context flag, not a formula penalty. It should drive deeper review and separate reporting in future component tests.