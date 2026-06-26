# NFL Usage Master Merge Package V0

Branch name: `work/nfl-usage-target-backtest-v0`.

Commit hashes: `ecebd8f` plus the follow-up historical expansion commit from this lane.

Allowed file areas touched: NFL usage historical panel docs, NFL usage target/backtest docs, NFL usage target/backtest services, scripts, and focused tests.

Files intentionally not touched: CFBD files, dependency files, app navigation, `/nfl-usage-evidence-review`, Settings/Data Health, Unified Universe Review, decision pages, model/rank/source-truth files, latest snapshots, frozen board, pinned snapshot.

Tests/checks: focused pytest, Ruff, Python compile, CSV load validation, diff check, raw/shared tracked scan, CFBD/dependency/app/model/rank guardrail scans, frozen board 66 rows, pinned hash unchanged.

Master integration risks: low code conflict risk because the lane is boxed; medium process risk because CFBD branch may add adjacent docs and should merge/reconcile separately.

Conflict expectations: expected only if another branch edits the same NFL usage target/backtest docs or services.

Recommended merge order with CFBD lane: reconcile CFBD first if it changes shared docs/indexes; then merge this branch; defer any UI review-page update to a dedicated post-reconciliation UI lane.

Post-merge smoke checks: run focused NFL usage target/backtest tests, CSV validation, guardrail scans, `/drafting-mode`, `/rankings`, and `/settings-data-health` browser smoke only if app files change later.
