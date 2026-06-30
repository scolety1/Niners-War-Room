# Trading Lab Schedule Context Test Report

Date: 2026-06-30

## Planned Checks

- focused Trading Lab tests
- `tests/test_trading_lab_nflverse_context_service.py`
- existing manual planner safe-upgrade tests
- schedule context display service tests
- Ruff on touched Python
- Python compile on touched Python
- `git diff --check`
- forbidden tracked path scan
- protected app/model/rank/source-truth scan
- route smoke `/trading-lab`

## Results So Far

- Focused tests: 32 passed
- Ruff on touched Python: passed
- Python compile on touched Python: passed
- Route smoke: `http://127.0.0.1:8575/trading-lab` loaded Trading Lab with 66 frozen-board rows, the NFLVerse display-only panel, manual planner tabs, and selected-item missing/deferred context.
- Selected-item route smoke: clicking Add Player rendered selected asset context, approved-details section, missing/deferred section, display-only/no-valuation labels, and the schedule gate copy.
- Note: Streamlit printed a pre-existing `use_container_width` deprecation warning during route smoke; no route failure was observed.
- `git diff --check`: passed.
- Protected path scan: passed.
- Narrow implementation scan for valuation/recommendation/offer/scoring/rank/source-truth mutation helpers: no hits.
- Broad forbidden-language scan found only guardrail copy and negative test assertions, not implementation paths.
- Schedule gate counts confirmed: 294 artifact rows, 240 safe schedule rows, 54 identity-review rows, 240 safe next-game rows, 240 safe opponent rows, and 240 safe bye rows.

## Assertions Covered

- Trading Lab schedule context appears only for safe player rows.
- Identity-review rows expose no schedule detail.
- Pick assets show no schedule context.
- Missing schedule data displays `Not enough information`.
- No valuation, trade timing, recommendation, package scoring, side totals, hidden sort, model input, market logic, pick value, injury risk, health inference, or medical projection appears.
- Trading Lab app page does not read raw `C:\NWR_SHARED_DATA`.
- Manual planner memo/export preserves the no-valuation disclaimer.

## Pending Before Commit

- final clean status after commit
