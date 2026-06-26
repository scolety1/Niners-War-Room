# NWR NFL Usage Target Label + Backtest V0 Plan

Purpose: create review-only factual next-season target labels and leakage-safe diagnostics for NFL usage fields.

Approved target source: factual historical NFL player statistics from nflverse/nflreadpy `player_stats` only.

Blocked target sources: ADP, market rank, DynastyProcess rank/value, projections, fantasy analyst ranks, current/candidate/manual rankings, RotoWire, CFBD, proxy drop rows, and unsupported Outcome gaps.

League scoring policy: 1QB, non-PPR; pass yards 1/30, pass TD 3, interception -1, rush/rec yards 1/10, rush/rec TD 4, rush/rec first down 0.4, return yards 1/30, return TD 4 via special teams TD where available, two-point conversion 2, fumble lost -1. K is excluded from usage backtest labels.

Target label definitions: next-season NWR points, points per game, games, positional rank, QB/RB/WR/TE top-threshold labels, starter-level buckets, and RB/WR/TE flex relevance.

Feature/target split: feature season N may join only to target season N+1. No target-season usage feature is allowed.

Leakage policy: no market/projection/rank fields, no current rankings, no target-season feature windows, no CFBD, and no vendor scrape inputs.

Minimum coverage: at least one complete feature season joined to the next factual target season for diagnostics; more seasons are required before model-candidate promotion.

Position-specific targets: QB top12, RB top12/top24, WR top12/top24/top36, TE top12, RB/WR/TE flex relevance.

Missing-data policy: missing factual scoring components are treated as zero only when the source omits that stat field; missing player rows are not fabricated.

No-CFBD boundary: this lane does not read, write, or depend on CFBD files or college/rookie evidence.

No-market/no-projection/no-rank target boundary: target truth is actual factual NFL production only.

No-model/no-app boundary: all outputs remain `model_input_allowed=no` and `app_wiring_allowed=no`; no app page or model integration is performed.

Parallel-lane safety policy: changes are boxed to `docs/hq/data_sources/nfl_usage/target_backtest/`, the two NFL usage target/backtest services, scripts, and focused tests.

Stop conditions: dirty branch, CFBD changes, dependency changes, app/navigation changes, source-truth/rank/model changes, insufficient factual labels, raw payload staged, or leakage violation.

Validation checklist: pytest, Ruff, compile, CSV load validation, diff check, raw/shared tracked scan, CFBD/dependency/app/model/rank/source-truth scans, frozen board row count, pinned hash.
