# Validation Results

## Determinism and focused checks

- Frozen preview replay: PASS; no output hash drift.
- Ruff on changed Python surfaces: PASS.
- Focused regression suite: 74 passed, 0 failed, 0 skipped.
- Preview: 320 visible rows; 304 ranked; 231 eligible veterans; 73 eligible
  rookies; 16 blocked and unranked.

## Complete repository suite

The complete suite finished in 489.45 seconds:

- 3,217 passed
- 279 failed
- 71 skipped

This is not reported as a green complete suite. Failures are dominated by legacy
lane tests that deliberately reject any `app/` working-tree change and historical
audits that require untracked `local_exports` absent from a fresh worktree. The
first failure is the expected dirty-app-path assertion; subsequent receipts include
missing local-only current-value files. Focused product and preservation tests are
green.

## Browser matrix

Real Streamlit browser checks passed at 375×812, 768×1024, and 1440×1000 for:

- Dynasty Rankings
- Player Compare
- Asset Explorer
- 2026 Rookie Board
- Trading Lab

All 15 route/viewport checks had the expected H1, no Page Not Found, no traceback,
no detected app exception, and no document-level horizontal overflow. Feature-level
checks confirmed the default production selector, research authority banner,
rookie neighborhoods, Player Compare production-scale disclaimer, Asset Explorer
opt-in default, and Trading Lab manual-only boundary. Blocking browser-console
errors: 0.
