# Historical Market / ADP Source Gate and Data Mart Join V1 Report

Verdict: `YELLOW_MARKET_ADP_FOUND_BUT_ASOF_GATE_NOT_PASSED`

Artifact path: `C:\NWR\Niners-War-Room-historical-market-adp-source-gate-data-mart-join-v1-20260709\docs\hq\model\historical_market_adp_source_gate_data_mart_join_v1_20260709`

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

Prior scoreboard normalization commit verified: `70be361e7d440d139af99c403f157b894f6e09c8`

## Executive Decision

Historical market / ADP data was found, but no candidate source passed the historical/as-of gate for review-only Formula Data Mart use. The lane therefore did not build a sidecar and did not run component, formula x ingredient, or bounded combination tests.

The strongest concrete market sources are:

- DynastyProcess public market cache and derived context from the `2026-06-19` scrape / `2026-06-23` NWR fetch.
- Sleeper ADP display-context candidate from the `2026` endpoint package collected on `2026-06-21`.
- Current-value, final-board, trading-lab, and rookie-market overlay artifacts from recovered local exports.
- Empty `player_market_inputs.csv` schema templates that include `season`, `asof_date`, and market fields but contain no source rows.

These are useful for future policy/source review, but they are not historical player-season market panels. Current-only ADP, current dynasty values, and current-board artifacts cannot be used as historical features.

## Candidate Source Counts

- Candidate rows ledgered: `220`
- Historical/as-of safe sources: `0`
- Likely historical but still needs proof: `0`
- Current/display-only or current-blocked sources: `88`
- Source-gate-required / identity-only / insufficient-information sources: `132`

## As-Of Classification Counts

- `CURRENT_ONLY_BLOCKED_FOR_HISTORICAL`: `28`
- `CURRENT_ONLY_DISPLAY`: `60`
- `NOT_ENOUGH_INFORMATION`: `112`
- `SOURCE_GATE_REQUIRED`: `20`

## Source / Use-Gate Counts

- `blocked_historical_formula_input`: `28`
- `display_only_market_context`: `60`
- `park_pending_manual_source_review`: `112`
- `policy_evidence_only`: `7`
- `requires_source_gate_before_use`: `13`

## Gate Result

Historical/as-of gate passed: `no`

Sidecar built: `no`

Component tests run: `no`

Formula x ingredient tests run: `no`

Ingredient combination tests run: `no`

## Why No Sidecar Was Built

The lane found no source that proves all of the following at once:

- player-season grain or a reliable transform to player-season grain
- market/ADP fields with row-level as-of dates
- historical coverage suitable for lagged 2013-2025 Formula Data Mart use
- source/use-gate approval for formula testing
- identity coverage sufficient for Formula Data Mart joins
- no current-only or same-season/future leakage

DynastyProcess and Sleeper are the clearest market sources, but both are current-context packages with explicit display-only / market-awareness constraints in existing NWR governance. They remain blocked as historical formula inputs.

## Scoreboard Impact

Because no sidecar was built and no tests were run, this lane produced no result that could beat the `.755` full-history plateau or the `.763` snap/depth broad-window reference.

Review-only ranking simulation remains `not justified`.

## Recommended Next Step

Recommended next lane: `Rookie Draft Capital Data Mart Join / Component Test V1`

Rationale: market/ADP needs a true historical/as-of source before it can be tested. Rookie/draft-capital data is more likely to help sparse-history and young-player false-negative problems without relying on current market snapshots.

## Preserved Gates

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- Push/merge was not performed.
- Source promotion was not performed.
- Canonical `local_exports` was not mutated.
- SportsDataIO, paid/API/free-trial/API-key work, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
