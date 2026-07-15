# Validation Results

## Baseline and focused set

- Remote fetch: PASS.
- Live HQ: `6bcb9c3c36fc560c30151591feaeff9d3960499f`; no advance.
- Clean baseline: `6 failed, 3 passed` across the exact nine nodes.
- Post-repair focused: `9 passed in 0.09s`.
- Focused skips/xfails: zero.

## Owning and broader regressions

Explicit owning/adjacent command covered Phase-5, Player Board, trust banners, Dynasty Rankings pages, Draft Prep, Draft Room checklist, Decision Trust Strip service/surface/render, navigation, Player Board score/value, and trust status.

Result: `100 passed, 14 skipped in 3.01s`. The fourteen skips are existing missing-local-pack sentinels. No focused node was included in the skips.

## Route, responsive, and accessibility

- `/rankings` HTTP: `200`.
- `375 × 812`: PASS; exact viewport and screenshot dimensions, zero Streamlit exceptions, no traceback/page-not-found, no root horizontal overflow.
- `1440 × 1000`: PASS; exact viewport and screenshot dimensions, zero Streamlit exceptions, no traceback/page-not-found, no root horizontal overflow.
- Decision Trust Strip AppTest and text-state/accessibility regressions: PASS.
- Browser plugin initialization: unavailable due bundled import error; local Chromium/CDP fallback passed.

## Static and code quality

- Python compilation: PASS.
- Changed-file Ruff: PASS.
- Full Ruff differential: zero new findings; one pre-existing touched-file formatting finding removed; untouched baseline findings remain.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS before local commit.

## Protection

- Security automation hashes/diff: PASS, unchanged.
- Protected-path scan: PASS, zero matches.
- Frozen-artifact byte/path scan: PASS, zero matches.
- Candidate inventory: three tests plus required packet only.

## Independent contract review

Verdict: `APPROVE`; unresolved findings: none.

1. Every changed expectation has canonical repository authority: PASS.
2. No application, model, service, data, ranking, formula, navigation, or UI behavior changed: PASS.
3. No test was weakened; assertions moved to current owners while retaining legacy and state-specific coverage: PASS.
4. Retained exact strings remain justified for governed states, current controls, trust labels, and Draft Prep gating: PASS.
5. Decision Trust Strip states and six-field ordering remain mechanically distinct and unchanged: PASS.
6. Negated language is not parsed by these repaired tests; the separate pre-existing security finding remains untouched: PASS.
7. Player Board routes, current labels, widget labels, and accessibility evidence agree: PASS.
8. Phase-5 governed wording and raw warning sources remain asserted on their owning legacy Decision Board: PASS.
9. No unrelated page or service changed: PASS.
10. Security automation and profile paths are unmodified and hash-identical to starting HQ: PASS.
11. Protected and frozen artifacts are unchanged: PASS.
12. The reviewer independently reran the exact nine nodes: `9 passed in 0.07s`, with no skip or xfail: PASS.

## Git disposition

- Local commit: created only after final independent review and staged checks.
- Push: not run.
- Merge: not run.
