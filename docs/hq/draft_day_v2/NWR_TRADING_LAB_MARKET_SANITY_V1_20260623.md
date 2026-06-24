# NWR Trading Lab Market Sanity V1 - 2026-06-23

## Final Verdict

GREEN.

Trading Lab now includes an optional DynastyProcess market sanity panel for manual give/get packages. The panel is display-only context and does not change NWR ranks, tiers, model values, trade verdicts, or source-truth artifacts.

## What Was Added

- Added service-level market helpers for Trading Lab:
  - `parse_trade_asset_text`
  - `lookup_pick_market_value`
  - `lookup_player_market_value`
  - `summarize_trade_package_market`
  - `classify_market_trade_gap`
  - display helpers for package rows and totals
- Added a Trading Lab expander titled `Market Baseline / Display-Only sanity check`.
- Added optional text inputs for manual pick/player assets on each side of a package.
- Added package-level market totals:
  - Give DP market total
  - Get DP market total
  - Difference
  - market sanity label
- Added DynastyProcess freshness and scrape-date display.

## Pick And Player Market Lookup

Pick lookup uses the existing `market_baseline_service` pick-value helpers instead of duplicating DynastyProcess loading in the page. Supported examples include:

- `2026 1.04`
- `2026 2.03`
- `2028 1st`
- `2028 2nd`
- `2027 3rd`

Player lookup joins selected Trading Lab player rows through the existing market baseline service. Missing player matches remain visible with `Not enough information`.

## Display-Only Guardrails

- DynastyProcess is labeled as market sanity only.
- Market values do not drive NWR rank, model value, or default sort.
- NWR trade verdicts remain separate from market totals.
- Unknown/manual assets stay visible as `REVIEW_NEEDED`.
- Missing market values show `Not enough information`, not zero.

## Missing-Data Behavior

Package totals exclude unmatched assets from numeric sums while separately counting unknown/review assets. If either side lacks usable market values, the market gap classification returns `Not enough information`.

## Tests And Checks

- `python -m pytest tests/test_draft_day_trade_lab_service.py tests/test_market_baseline_service.py`
- `python -m ruff check src/services/draft_day_trade_lab_service.py app/pages/23_trading_lab_v1.py tests/test_draft_day_trade_lab_service.py src/services/market_baseline_registry.py`
- `python -m py_compile src/services/draft_day_trade_lab_service.py app/pages/23_trading_lab_v1.py tests/test_draft_day_trade_lab_service.py`
- `git diff --check`

Focused tests cover pick parsing, player lookup, missing market matches, package totals, unknown asset handling, display-only registry usage, and Trading Lab operation without market data.

## Browser Smoke

Browser smoke confirmed the core app pages still open:

- `/trading-lab`
- `/rankings`
- `/live-draft-room`
- `/cheat-sheets`
- `/post-draft-mode`
- `/player-compare`
- `/mock-draft`

Trading Lab confirmed:

- existing give/get builder still renders
- display-only market panel renders
- give/get manual market asset inputs render
- service-level tests confirm package example `2026 1.04` for `2026 2.03 + 2028 1st`
- service-level tests confirm market totals render when values are available
- missing/unknown assets remain visible for review

## Known Limitations

- DynastyProcess remains a market baseline, not NWR truth.
- Future-pick values are only as good as the available market baseline artifact.
- The panel is a sanity check, not a trade calculator and not final trade advice.
- Unknown free-text assets require human review.
