# Validation Results

Focused engine, roster, authority-preservation, and Trading Lab tests: 71 passing. Ruff and
Python compilation: passing.
Owner-case local replay reproduces `COUNTER — MEDIUM`, current-side preference, the exact
ownership conflict, partial DP totals 4,443 vs 3,495, and zero named counters.

Browser review passed at 375×812, 768×1024, and 1440×1000 with document/body scroll width equal
to viewport width. Required owner-facing answers were visible without opening Advanced Data
Details. Team-window comparison showed all three views. A disposable advisory receipt survived
a process restart with exact sides and immutable source snapshot.

Adoption remains blocked by the actual counterparty acceptance test, not by a runtime defect:
the admitted roster evidence cannot establish one counterparty or 2027/2028 pick ownership.

The broader repository run completed with 3,269 passed, 53 skipped, and 329 failed. The failure
set is not represented as green: it includes dirty-worktree sentinel tests, tests requiring
generated/local model artifacts outside this lane, pre-existing trust-banner expectation
drift, and superseded manual-only Trading Lab assertions. Feature-relevant superseded tests
were updated and now pass in the 71-test focused gate; unrelated baseline failures remain a
repository limitation and are one reason this lane is not canonicalized.
