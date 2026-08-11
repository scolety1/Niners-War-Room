# Validation Results

- Focused changed-surface suite: 110 passed after final presentation refinements.
- Exact numeric regression fixture: PASS ascending, descending, and missing-last.
- Actual browser grid: eight required numeric columns PASS ascending/descending.
- Exact four-asset trade: PASS compose, analyze, save, reload, reopen, prepare Markdown/JSON, and removal propagation.
- Responsive matrix: 12/12 route/viewport combinations, zero Streamlit exceptions and zero root overflow.
- Full repository attempt: 3,237 passed, 71 skipped, 321 failed in 532.99 seconds. The failures are dominated by legacy tests that require a clean worktree while this lane necessarily changes `app/`, or hardcode ignored `local_exports` paths absent from isolated worktrees. This result is disclosed and is not represented as green.
- Formatting, lint, compile, diff check, preservation, fresh adoption, and remote receipts are appended at finalization.

Focused implementation commit: `10c9d0e6c8c9fd06f5a7b8507c2556a226ee15df`.
