# NWR NFL Usage Source Contract V0

## Status

Research-only. No field in this contract is approved for model input, app wiring, ranking changes, source-truth mutation, Dynasty Rank mutation, Final Board Rank mutation, tier mutation, latest_candidate update, latest_approved update, or pinned snapshot mutation.

## Allowed Sources

- nflverse/nflreadpy or nflreadr-equivalent public structured data.
- Public nflverse release files when accessed through project-approved scripts.
- Player stats, play-by-play, snap counts, Next Gen Stats, participation, FTN charting subset, PFR advanced stats, rosters, and ID crosswalks.
- Existing local project templates only when they are review-only and source-attributed.

## Blocked Sources

- RotoWire live scraping or crawling.
- Any blocked vendor site scraping.
- Vendor projections, rankings, values, analyst blurbs, start/sit grades, betting odds, DFS salaries, ADP, trade values, market values, or proprietary scores.
- Raw payloads committed to Git.

## Raw Cache Policy

Raw nflverse payloads must live outside the repo at `C:\NWR_SHARED_DATA\nfl_usage_cache\`. Large normalized player-week/play data must stay in shared data or `local_exports`, both untracked. Only small sanitized review summaries may be committed.

## Field Truth Labels

- `TRUE_FACTUAL_FIELD`: directly factual public structured field.
- `TRUE_DERIVED_FACT`: transparent arithmetic/count from factual rows.
- `DERIVED_PROXY`: approximation or share metric requiring caveat.
- `LICENSED_DATA_GAP`: useful field exists only in licensed or unverified sources.
- `BLOCKED_UNSAFE`: field is unsafe, opinion/vendor/rank/market/projection, or legally blocked.
- `NOT_EVALUATED`: not yet introspected or approved.

## Proxy Versus True Policy

Public participation data is not automatically true routes run. Route-related values, TPRR-like values, and YPRR-like values must stay proxy-labeled unless exact full route-run data is verified from an approved source.

## Promotion Gate

Promotion requires explicit provenance, stable schema, coverage, no leakage, missing-data handling, validation/quarantine pass, attribution compliance, and backtest proof. V0 grants no promotion.
