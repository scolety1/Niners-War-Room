# Validation Results

- Focused changed-surface suite: 110 passed after final presentation refinements.
- Exact numeric regression fixture: PASS ascending, descending, and missing-last.
- Actual browser grid: eight required numeric columns PASS ascending/descending.
- Exact four-asset trade: PASS compose, analyze, save, reload, reopen, prepare Markdown/JSON, and removal propagation.
- Responsive matrix: 12/12 route/viewport combinations, zero Streamlit exceptions and zero root overflow.
- Full repository attempt: 3,237 passed, 71 skipped, 321 failed in 532.99 seconds. The failures are dominated by legacy tests that require a clean worktree while this lane necessarily changes `app/`, or hardcode ignored `local_exports` paths absent from isolated worktrees. This result is disclosed and is not represented as green.
- Formatting, lint, compile, diff check, preservation, and fresh adoption: PASS.
- First canonical push receipt: `974f163dbad8c323b7ade25d5fe8983f82a8df22..bd3a54f03baf83904cab78fed55c1c8cf68e0580`, normal fast-forward to `origin/work/hq-parallel-control`.
- Canonical product tree: `5fdad44d772748433318e43a224be4481c51d583`.
- Stable focused replay: 110 passed in 8.82 seconds.
- Stable owner workflow replay: PASS exact four assets, no Brock Purdy, useful interpretation, save/reload/reopen, export preparation, and removal propagation; zero errors or exceptions.
- Stable launcher: healthy after launch from the canonical code, then stopped through verified ownership; port released and ownership state cleared.
- Existing Streamlit `use_container_width` deprecation messages remain console-only and did not affect rendered acceptance.
- Cleanup receipt: the stable replay's only saved-scenario file was removed; no pre-existing owner record existed, and the personal scenario store was absent at the final gate.

Focused implementation commit: `10c9d0e6c8c9fd06f5a7b8507c2556a226ee15df`.
Fresh adoption documentation commit: `bd3a54f03baf83904cab78fed55c1c8cf68e0580`.
