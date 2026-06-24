# NWR Dynasty Rankings Market Baseline Integration V1 - 20260623

## Verdict
GREEN.

## Starting Master HEAD
`3100a92a3c81910a33677117e688fd07a67b6dae`

## Purpose
Integrated optional DynastyProcess market baseline context into the Dynasty Rankings page as display-only market sanity context. This does not change Dynasty Rank, Final Board Rank, Candidate Rank, tier assignments, source truth, or model logic.

## Files Changed
- `app/pages/20_final_board_v1.py`
- `src/services/draft_day_app_v1_service.py`
- `src/services/market_baseline_registry.py`
- `src/services/market_baseline_service.py`
- `tests/test_dynasty_rankings_page_v1.py`
- `tests/test_market_baseline_service.py`
- `docs/hq/parallel_lanes/NWR_DYNASTY_RANKINGS_MARKET_BASELINE_INTEGRATION_V1_20260623.md`

## Market Fields Added
Hidden by default behind `Show Market Baseline columns`:

- `DP 1QB Value (Market Baseline / Display-Only)`
- `DP 1QB Market Rank (Market Baseline / Display-Only)`
- `DP ECR Pos (Market Baseline / Display-Only)`
- `DP Age (Market Baseline / Display-Only)`
- `NWR vs Market Gap (Market Baseline / Display-Only)`
- `Market Sanity Flag (Market Baseline / Display-Only)`
- `Age Source`
- `Market Baseline Label`

## Hidden By Default
The default Dynasty Rankings table remains clean:

- default view: `Full Dynasty Rankings`;
- default sort: `Dynasty Rank` ascending;
- default positions: `QB`, `RB`, `WR`, `TE`;
- K/DST hidden by default;
- no Final Board Rank, source coverage, draft action, DynastyProcess, or market columns in the default table;
- market columns appear only when the user enables the toggle.

## Market Sanity Filters
Added display-only filters:

- Market sanity: `All`, `NWR much higher`, `NWR much lower`, `Aligned`, `No market match`;
- Market match: `All`, `Has market match`, `No market match`.

Unmatched players remain visible unless the user explicitly filters them out.

## Join Coverage
Service-level coverage against the approved 240-row full dynasty board:

- rows: 240;
- market matches: 232;
- no market match: 8.

The join is performed through `src/services/market_baseline_service.py`; page-level code does not duplicate the join logic.

## Age Coverage
Age coverage against the approved 240-row full dynasty board:

- NWR age coverage before market fallback: 224;
- after display-only market fallback: 240;
- DynastyProcess display-only age fallback rows: 16.

Rows filled by market fallback are labeled `Market Baseline / Display-Only fallback` in the optional market columns. This is display context only and does not mutate the approved dynasty source.

## Freshness Status
Market baseline freshness:

- freshness status: `GREEN_CURRENT`;
- upstream scrape date: `2026-06-19`;
- upstream latest commit: `a38911c0080e5623741eaa3bfcd63d1db98a5342`;
- NWR fetch timestamp: `2026-06-23T22:37:05+00:00`.

## Display-Only Confirmation
DynastyProcess market baseline is display-only:

- not a model input;
- not a rank input;
- not a Candidate Rank input;
- not a hidden sort input;
- not source truth;
- not used to overwrite Dynasty Rank, Final Board Rank, or tier assignment.

Registry confirmation: `dynasty_rankings` market usage is enabled, `default_visible=False`, `sort_allowed=False`, and `model_input_allowed=False`.

## Known Caveat
The approved full dynasty source currently has 0 rookie/prospect rows. Rookies/prospects remain available through the draft-board/unified views where supported, but this task did not add rookies/prospects to the 240-row approved full dynasty source.

## Tests And Checks
Validation passed:

- focused pytest: `64 passed`;
- Ruff on touched Python files: PASS;
- Python compile on touched Python/test files: PASS;
- `git diff --check`: PASS;
- frozen board row count remains 66;
- pinned manifest hash unchanged: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`;
- latest candidate/latest approved untouched;
- no `C:\NWR_SHARED_DATA` files tracked;
- no raw vendor files tracked;
- no prediction dumps tracked.

## Browser Smoke
Local Streamlit preview: `http://127.0.0.1:8526`

Passed:

- `/rankings`: opens; Full Dynasty Rankings is default; 240 full dynasty rows visible in status; 232 rows shown after current default filtering; K/DST hidden by default; Market Baseline status/filters visible; market columns hidden by default; toggle shows display-only caption; baseline/checkpoint wording preserved;
- `/cheat-sheets`: opens; tiered board polish preserved;
- `/drafting-mode`: opens;
- `/live-draft-room`: opens; active draftable pool / frozen baseline wording preserved;
- `/player-compare`: opens;
- `/trading-lab`: opens;
- `/mock-draft`: opens.

Service-level player proof:

- Puka Nacua Dynasty Rank: 1;
- Zay Flowers Dynasty Rank: 12.

Streamlit virtualizes dataframe cells, so exact market column headers and player rows were also verified through service/unit tests rather than only DOM extraction.

## Remaining Issues
None blocking. Known data caveat only: 0 rookie/prospect rows in the approved full dynasty source.
