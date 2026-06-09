# Report Contradictions And Weak Recommendations

Date: 2026-05-07

Scope:

- `2026-05-07_public_structured_data_stack.md`
- `2026-05-07_final_stats_first_veteran_model.md`

Purpose:

Flag issues **before touching formulas**. This file is a guardrail: do not blindly implement a formula or data dependency from either report until the related issue below is resolved.

## Executive Verdict

The reports are directionally strong: they correctly push the app toward nflverse/ffverse data, local LVE scoring, market isolation, WR/RB demand, QB/TE suppression, and review-only gates.

But several recommendations are too aggressive, underspecified, or internally inconsistent. The biggest risks are:

- treating weak or unavailable public data as if it were model-ready
- double-counting VOR, projections, actual production, and market liquidity
- letting forced-release rules leak into player quality
- hardcoding named player sanity checks into the model instead of using them as audit tests
- using 2018-2025 normalization distributions while also claiming 2025 is a held-out test year

## Highest-Priority Blocks

| status | issue | why it matters | recommended policy before coding |
|---|---|---|---|
| Block | Normalization leakage: the model report says use 2018-2025 training distributions, then says train 2018-2023, validate 2024, test 2025. | If 2025 is inside the percentile distribution, 2025 is not a clean test. That contaminates backtesting. | For current/live 2026 model, use the full historical distribution allowed by date. For historical replay, build as-of distributions only through the season available at that time. |
| Block | Current injury feed gap conflicts with current-health and durability formulas. | The data-stack report says nflverse injuries are 2009-2024 in practice and have no 2025+ feed. The model report still depends on `current_health_flag`. | Treat current health as optional/manual/source-specific. If missing, cap durability and lower confidence, but do not create fake injury certainty. |
| Block | Route participation is caveated, but formulas use route/target involvement as mandatory TE/WR logic. | Data-stack report says participation is not true routes run and 2023+ is season-end only. The model report uses `route_rate_proxy_score` in TE exception and role buckets. | Mark route fields as proxy. Do not let route proxy alone unlock elite TE/WR gates. Require target share, snap share, and actual/expected production agreement. |
| Block | Several formula fields do not have a legal/free structured source in the data-stack report. | `qbr_score`, `ryoe_per_att_score`, `separation_score`, `yac_oe_score`, `contract_years_remaining`, and some projection fields are not guaranteed by the recommended free stack. | Keep these optional/display-only until a legal export source is chosen. Do not make them required core features. |
| Block | Active formulas include `forced_release_penalty` inside keeper scores. | Forced release is a league rule and availability/action constraint, not player quality. User clarified every team releases one top-five league-rank player. | Split `player_value` from `rule_pressure`. Keeper score should not be reduced by forced-release rule; action recommendations can show release pressure separately. |

## Data Source Contradictions / Weak Spots

### 1. "Minimum viable stack" versus formulas requiring optional enrichment

The data-stack report's minimum viable stack is:

`player_stats + pbp + players + rosters_weekly + ff_playerids + snap_counts`, with `ff_opportunity` as expected opportunity.

The final model then asks for:

- contract security score (`CSC`)
- ESPN QBR
- RYOE per attempt
- receiver separation
- YAC over expected
- current health flag
- market rank position
- FantasyPros ID

Some of those are not in the minimum stack and may not be available as legal structured exports without extra work or paid sources.

Policy:

- Core model v1 should use only fields that are actually imported.
- Optional enrichment fields should be neutral/imputed and confidence-penalized.
- Do not let an optional enrichment field become a hard gate.

### 2. RDS-only sources conflict with CSV-first local workflow

The data-stack report notes that some valuable sources are effectively RDS-only from documented loader paths:

- `load_depth_charts`
- `load_ff_playerids`
- `load_ff_opportunity`

Policy:

- Implement a source adapter/export step, not direct runtime dependence on RDS.
- Persist local CSV snapshots after conversion.
- The app runtime should only read local CSV/JSON.

### 3. Play-by-play is valuable but too heavy to make every run blocking

The data-stack report correctly recommends PBP for exact re-derivation and validation. But requiring PBP before any model preview would slow down the workflow and create a huge local data burden.

Policy:

- Weekly player stats are the first scoring source.
- PBP is an audit/validation layer.
- PBP mismatch should trigger review, not block every normal refresh unless the weekly stats are missing first-down fields or totals fail validation.

### 4. Expected opportunity has uncertain release timing

The data-stack report says `ff_opportunity` releases exist but does not give the same clean SLA as nflverse stats/PBP. The model gives expected opportunity heavy influence.

Policy:

- Track `source_release` and `ingested_at_utc`.
- If expected opportunity is stale/missing, lower confidence and shift weight toward historical/projection/role layers.
- Do not silently use stale expected-opportunity data.

### 5. Market source is underspecified

The model report uses `market_rank_pos`, `M_score`, and market-edge formulas, but neither report gives a fully settled legal export source for market ranks.

Policy:

- Market data remains optional.
- Market cannot affect `private_lve_value`.
- Market edge should be unavailable or low-confidence if market source is missing.

## Formula Contradictions / Weak Spots

### 6. VOR is probably double-counted

The final model includes VOR inside position historical buckets:

- `H_RB = ... + 0.20*VOR_RB`
- `H_WR = ... + 0.20*VOR_WR`
- `H_TE = ... + 0.20*VOR_TE`

Then it also includes VOR directly in keeper scores:

- RB keeper has `0.16*VOR_RB`
- WR keeper has `0.18*VOR_WR`
- TE keeper has `0.18*VOR_TE`
- QB keeper has `0.15*VOR_QB`

Risk:

VOR can inflate the same projected PPG edge twice, especially for WR/RB cross-position ordering.

Policy:

- Put VOR in one place only.
- Preferred: keep VOR out of H/private buckets and use it as an explicit keeper/acquisition context layer.

### 7. WR +5 private adjustment may double-count lineup demand

The report adds `+5` to WR private value because LVE starts 3 WR and 2 flex. But replacement baselines already use `WR46`, which should capture deep WR demand.

Risk:

WRs can be boosted by both:

- lower/deeper replacement line
- flat +5 private adjustment

Policy:

- Use either VOR replacement line or flat WR context bump, not both at full strength.
- Prefer replacement-line/VOR math because it is more auditable.

### 8. QB passing first downs are context, not scoring

The data report says passing first downs may be imported for context but are not scored in LVE. The model uses `pass_first_down_pg_score` as 50% of `F_QB`.

Risk:

Pocket passers can get hidden help from a non-scoring stat, weakening the 1QB / 3-point passing TD suppression.

Policy:

- Passing first downs can stay in QB efficiency/context at low weight.
- Do not let passing first downs drive the main LVE fantasy fit bucket.
- QB rushing and actual/projected LVE points should dominate the fantasy-scoring side.

### 9. Expected interception term is unresolved

The model formula includes `pass_int_exp * int_pts`, then immediately says to leave expected turnovers out if not defensible.

Policy:

- Do not require `pass_int_exp`.
- Expected LVE points v1 should exclude expected turnovers unless a reliable source is imported.
- Historical interceptions can remain in actual LVE points and volatility/efficiency.

### 10. Market edge formula includes market twice

The model says:

`market_edge_score = clamp(50 + 0.70*(private_lve_value - market_rank_score) + 0.30*(M - 50), 0, 100)`

But `M` itself is market rank plus liquidity prior.

Risk:

Market edge is supposed to measure private model disagreement with market. Adding `M` can muddy the interpretation and partially reward market popularity inside an edge score.

Policy:

- Use a simple primary edge: `private_lve_value - market_value`.
- Show liquidity separately as "can this edge be traded?"
- Do not blend liquidity into the disagreement score.

### 11. Drop candidate score uses market liquidity

The model includes `100 - M` inside drop candidate score.

This can be useful if the question is "drop versus shop," but it is misleading if the column is read as "football cut risk."

Policy:

- Split into:
  - `football_cut_risk`
  - `shop_before_cut_signal`
  - `final_drop_action`
- Market liquidity should reduce "drop now" urgency, not improve player quality.

### 12. Forced-release penalty inside keeper score is wrong for LVE semantics

The reports use `forced_release_penalty`, but LVE's forced top-five release rule is a roster-management constraint. It does not make a player worse at football.

Policy:

- Keep `private_lve_value`, `keeper_score`, and `trade_value` player-centric.
- Compute forced-release pressure separately.
- The action panel can say: "Great player, but rule forces one top-five release."

### 13. Projection source is not settled

The final model gives projections meaningful weight, especially in win-now outputs. The public data-stack report is mostly about historical/source data and does not settle a free/legal projection source.

Policy:

- `P_score` is optional until projection import is stable.
- If projection data is missing, redistribute weight to historical expected/actual and lower confidence.
- Do not use scraped projections.

### 14. Contract security is not settled

The model uses `CSC`, and source links include OverTheCap. The data-stack report does not establish a legally exportable structured contract import.

Policy:

- Contract score should be optional v2.
- If used now, keep it display-only or low-weight manual input with provenance.

### 15. Advanced efficiency fields are not guaranteed

The model references:

- `qbr_score`
- `ryoe_per_att_score`
- `separation_score`
- `yac_oe_score`
- `yprr_proxy_score`

The public data stack treats NGS as optional and threshold-filtered, and source links like ESPN QBR / PFR advanced tables may not be safe structured imports without manual export or licensing review.

Policy:

- Make advanced efficiency optional.
- Build v1 efficiency from nflverse actual/expected deltas, yards per opportunity, first-down rate over expectation, and EPA context where available.
- Do not block the model on ESPN/PFR/NGS enrichment.

## Calibration / Test Weak Spots

### 16. Named player sanity fixtures can become overfit

The final model names Kyren/Bijan/Gibbs/Jeanty, JSN/Tee, BTJ/Luther, and Chase Brown/Luther. These are useful smoke tests because they caught real absurd outputs.

Risk:

If they become tuning targets, the model can become "make these names rank right" instead of a general statistical model.

Policy:

- Use named fixtures as guardrails and receipt checks.
- Require the ranking difference to be explained by raw stats/features.
- Do not add player-specific overrides to satisfy a fixture.

### 17. Backtest targets require data the app may not have

The model proposes:

- keeper score -> top-230 roster survival
- drop candidate -> next 12 months roster-cut probability
- trade value -> production plus liquidity execution

These are good ideas, but they require historical LVE roster/declaration/drop/trade data that public nflverse does not provide.

Policy:

- Use public fantasy outcomes for first-pass calibration.
- Use LVE history only where you have actual league records.
- Mark local-history calibration incomplete until the data exists.

### 18. Private value target may overrate fragile per-game assets

The report maps `private_lve_value` to next-season LVE points per active game. That is useful, but per-active-game targets can overrate players who miss many games.

Policy:

- Keep per-game production in private value.
- Also include durability/availability and VOR in keeper/acquisition value.
- For backtesting, evaluate both active-game PPG and total VOR.

## Schema / Implementation Weak Spots

### 19. Two different schema philosophies exist

The data-stack report proposes:

- `dim_player_ids.csv`
- `dim_players.csv`
- `fact_player_week_stats.csv`
- `fact_player_week_usage.csv`
- `fact_player_week_health.csv`
- `fact_player_week_xfp.csv`

The model report proposes:

- `lve_player_inputs.csv`
- `lve_bucket_scores.csv`
- `lve_model_outputs.csv`

These are not contradictory if layered correctly, but they should not be merged into one confused table.

Policy:

- Raw source layer: `dim_*` and `fact_*`.
- Derived model input layer: `lve_player_inputs.csv`.
- Audit layer: `lve_bucket_scores.csv`.
- Output layer: `lve_model_outputs.csv`.

### 20. `player_id_mfl` / `player_id_fantasypros` are not core for LVE

The final model schema includes MFL and FantasyPros IDs. The user's operational app uses Sleeper and nflverse.

Policy:

- Required IDs: `gsis_id`, `sleeper_id`, `pfr_id` where needed for snap counts.
- Optional IDs: MFL, FantasyPros, ESPN, PFF.
- Do not block model use because MFL/FantasyPros IDs are missing.

### 21. Legal/export posture needs enforcement in code

The data report is clear: avoid brittle scraping, preserve attribution, and respect FTN-derived share-alike data.

Policy:

- Importers should only support local files or known public release URLs.
- No generic website scraping.
- Add source attribution fields to every imported table.

## Recommended "Do Not Touch Formulas Until" Checklist

Before changing formula coefficients, finish these policy decisions:

1. Decide whether 2025 is inside normalization training or held out for testing.
2. Decide how missing current injury data affects durability and confidence.
3. Decide whether route proxies can unlock elite TE/WR gates.
4. Decide whether VOR lives in private buckets or keeper/acquisition only.
5. Decide whether WR gets a flat +5 when WR46 replacement already exists.
6. Decide whether passing first downs are low-weight QB context only.
7. Decide whether market edge is simple private-minus-market.
8. Decide whether drop score splits football cut risk from shop-before-cut.
9. Decide whether forced-release pressure is separate from keeper value.
10. Decide which optional enrichment fields are v1, v2, or display-only.

## Safe Implementation Defaults

Until those decisions are made:

- Keep formulas review-only.
- Use only imported nflverse/ffverse core data for private value.
- Treat current injury, route-rate, contract, QBR, RYOE, separation, YAC OE, and projections as optional.
- Keep market out of private value.
- Keep league rank and forced release out of player quality.
- Use named player fixtures as audit alarms, not training labels.

