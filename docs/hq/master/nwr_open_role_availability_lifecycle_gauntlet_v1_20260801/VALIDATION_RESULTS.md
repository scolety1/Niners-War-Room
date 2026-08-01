# Validation Results

- Formula Data Mart authority: PASS, exact 5,518 rows and immutable LF-canonical hash.
- Age/lifecycle authority: PASS with unsafe or unresolved identity rows retained as unknown.
- Five-family preregistration: PASS; no unregistered family or tuning sweep executed.
- Three separate target horizons: PASS; Win Now t0, two-year t1, and three-year t2 remain distinct and horizon-closed.
- Same-row PYF comparison: PASS across 39 applicable family/position/horizon cells.
- Chronological evaluation: PASS with six to eight eligible test seasons after five prior anchor seasons.
- Deterministic season-block bootstrap: PASS, 2,000 repetitions per cell.
- Multiple-comparison control: PASS mechanically; no family cleared all gates after Holm correction.
- Productive-veteran and low-games protection: PASS as enforced family gates; two families failed at least one protection gate.
- Outcome: truthful null, `NULL_NO_FAMILY_PASSED`; zero families promoted.
- Production changes, provider calls, rankings, and recommendations: zero.
- Focused and applicable regressions: PASS, 106/106.
- Ruff, compile, and Git whitespace checks: PASS.
- Independent adoption review: PASS in a fresh worktree from the exact canonical parent; implementation and adopted trees matched byte-for-byte, deterministic regeneration returned the same null result, 106/106 regressions passed, and Ruff passed.
