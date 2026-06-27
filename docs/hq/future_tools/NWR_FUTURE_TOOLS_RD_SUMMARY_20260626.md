# NWR Future Tools R&D + Safe Scaffold Summary - 2026-06-26

## Verdict

GREEN as an R&D/spec/status scaffold. No Future Tool was launched as an active recommendation, model output, ranking, projection, trade target, waiver recommendation, start/sit answer, or source-truth decision.

## What Changed

- Added a Future Tools status matrix with 14 tools across In-Season Tools, Future Draft Prep, and League Calendar Tools.
- Added one per-tool R&D spec under `docs/hq/future_tools/tool_specs/`.
- Added a local source inventory explaining what data is display-only, review-only, blocked, or manual/privacy-gated.
- Updated `/future-tools` into a roadmap/R&D control board backed by the committed status matrix.
- Added focused tests for the matrix and page guardrails.

## Tool Decisions

| Tool | Decision | Safe Current Use |
|---|---|---|
| Who Should I Start? | BLOCKED_NEEDS_MODEL_GATE | Roadmap only |
| Waiver Wire Rankings | BLOCKED_NEEDS_DATA | Roadmap only |
| In-Season Rankings | BLOCKED_NEEDS_MODEL_GATE | Roadmap only |
| Trade Targets | BLOCKED_NEEDS_MODEL_GATE | Roadmap only |
| Roster Weakness Tracker | SAFE_NOW_FRAMEWORK_ONLY | Descriptive checklist shell only |
| Upcoming Rookie Class Preview | BLOCKED_NEEDS_HUMAN_APPROVAL | Roadmap only |
| Draft Class Strength | BLOCKED_NEEDS_MODEL_GATE | Roadmap only |
| Position Strength by Class | BLOCKED_NEEDS_MODEL_GATE | Roadmap only |
| Future Pick Planning | SAFE_NOW_FRAMEWORK_ONLY | Manual/event-log inventory shell only |
| Position Target Plan | BLOCKED_NEEDS_MODEL_GATE | Roadmap only |
| Keeper Deadline Prep | SAFE_NOW_FRAMEWORK_ONLY | Checklist shell only |
| Drop Deadline Prep | SAFE_NOW_FRAMEWORK_ONLY | Checklist shell only |
| Trade Deadline Prep | SAFE_NOW_FRAMEWORK_ONLY | Checklist shell only |
| Playoff Push Planner | BLOCKED_NEEDS_DATA | Roadmap only |

## Source And Gate Findings

- Sleeper can support league, roster, draft, pick, and traded-pick context in future work, but no data refresh or new connector behavior was run in this lane.
- nflverse/nflreadpy can support future NFL usage research, but current NFL usage evidence remains review-only and not model input.
- CFBD remains review-only with identity/human approval gates.
- DynastyProcess/ADP/market data remains display-only and cannot drive recommendations, trade value, hidden sort, or model value.
- RotoWire/vendor/Gmail automation remains blocked/manual.
- True routes, true TPRR, and true YPRR remain licensed-data gaps unless an approved licensed source exists.

## Page Guardrails

The `/future-tools` page now says:

> Roadmap and R&D only. These are not active model outputs, projections, rankings, start/sit recommendations, waiver recommendations, trade targets, or source-truth decisions unless explicitly marked as a safe display-only scaffold.

The status matrix keeps `active_output_allowed=no` and `model_input_allowed=no` for every row.

## External Research References

- Sleeper API docs: https://docs.sleeper.com/
- nflreadpy: https://github.com/nflverse/nflreadpy
- nflreadr play-by-play docs: https://rdrr.io/cran/nflreadr/man/load_pbp.html
- nflreadr snap counts docs: https://rdrr.io/cran/nflreadr/man/load_snap_counts.html
- CollegeFootballData: https://collegefootballdata.com/
- DynastyProcess data: https://github.com/dynastyprocess/data

## Guardrails

- No rank, tier, Dynasty Rank, Final Board Rank, frozen-board, pinned snapshot, latest candidate, latest approved, source-truth, or model logic changes.
- No model input promotion.
- No CFBD/NFL usage promotion.
- No decision-page wiring.
- No data refresh.
- No hosted deployment.
- No raw/shared/local/secret files tracked.

## Validation

- Focused pytest: `27 passed`.
- Ruff on touched Python/tests: passed.
- Python compile on touched Python/tests: passed.
- CSV load validation: status matrix 14 rows; tool inventory 14 rows.
- `git diff --check`: passed.
- Browser smoke on port 8608: `/future-tools`, `/live-draft-room`, `/mock-draft`, `/rankings`, `/trading-lab`, `/post-draft-mode`, `/settings-data-health`, `/player-compare`, `/refresh-data`, and `/evidence-integration-review` rendered without traceback.
- Frozen baseline board row count: 66.
- Protected artifact diff paths: none.

## Remaining Caveats

- Framework-only shells are not active features; they show prep/checklist structure only.
- Any active Future Tool requires a later explicit model/data/source-truth gate.
- Human review remains required before CFBD/unified rookie evidence can support product decisions.
