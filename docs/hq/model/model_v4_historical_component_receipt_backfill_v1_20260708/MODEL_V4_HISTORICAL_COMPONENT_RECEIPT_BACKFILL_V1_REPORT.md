# Model v4 Historical Component Receipt Backfill V1 Report

## Verdict

`YELLOW_MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS_PARTIAL_WITH_BLOCKERS`

## Clear Answer

Exact Model v4 historical replay is not now possible because the exact season-by-season checkpoint, lifecycle, confidence, candidate-overlay, and normalized component receipt chain still does not exist. This lane backfilled `42933` review-only historical partial receipts from the existing lagged V3 factual overlap panel, but those receipts are proxy/source-availability receipts only and must not be treated as exact Model v4 scores.

## What Was Backfilled

- Current component targets reviewed: `46`.
- Components with partial historical receipt analogs: `19`.
- Components still exact-replay blocked: `19`.
- Components excluded from replay: `8`.
- Review-only player/component receipt rows backfilled: `42933`.
- Historical panel source SHA256: `dd5897cd215f501af57d9d30ab27020d981ae8da505eb05245c5f992a7fea44a`.
- Season coverage: `2013-2025`.
- Position receipt rows: `{'QB': 6032, 'RB': 11432, 'TE': 8477, 'WR': 16992}`.

## Historical Replay Readiness

| Season Range | Position | Required Components | Available | Blocked | Replay Status | Main Blocker |
| ------------ | -------- | ------------------: | --------: | ------: | ------------- | ------------ |
| 2013-2025 | QB | 21 | 8 | 13 | partial replay possible; exact blocked | missing current QB component receipts, age/role lifecycle receipts, and candidate old-pocket overlay history |
| 2013-2025 | RB | 18 | 8 | 10 | partial replay possible; exact blocked | missing current RB component receipts for role/red-zone/efficiency plus lifecycle/confidence history |
| 2013-2025 | WR | 19 | 8 | 11 | partial replay possible; exact blocked | missing current WR route/YPRR/air-yard/stats-first receipts plus candidate overlay history |
| 2013-2025 | TE | 19 | 7 | 12 | partial replay possible; exact blocked | missing TE route/YPRR/red-zone receipts and TE discipline/lifecycle/confidence history |

## Component Receipt Coverage

See `MODEL_V4_HISTORICAL_RECEIPT_COVERAGE_SUMMARY.csv`.

## Known Blockers

See `MODEL_V4_HISTORICAL_COMPONENT_BLOCKERS.md`.

## Benchmark Contract

See `MODEL_V4_NEXT_REPLAY_BENCHMARK_CONTRACT.md`. The next benchmark can only be a partial historical replay benchmark unless exact Model v4 historical receipts are recovered first.

## Production Status

- Current board remains review-only.
- Exact current-board rebuild remains verified.
- Production-active status remains blocked.
- Historical accuracy remains unproven until a separate benchmark is run.
- No source was promoted by this lane.
- No ranking output, model weight, app behavior, or canonical `local_exports` file was changed.

## Recommended Next Lane

`Partial historical replay benchmark`

This should benchmark only the partial lagged receipt panel against baselines and must state that it is not exact Model v4 replay. Exact replay still requires additional historical source/receipt recovery.
