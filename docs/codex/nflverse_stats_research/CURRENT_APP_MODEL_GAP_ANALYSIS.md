# Current App / Model Gap Analysis

Date: 2026-05-07

Compared reports:

- `2026-05-07_public_structured_data_stack.md`
- `2026-05-07_final_stats_first_veteran_model.md`
- Extracted contract: `IMPLEMENTATION_REQUIREMENTS.md`

Compared implementation:

- Active app data pack: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`
- Active visible model outputs: `model_outputs.csv`
- New stats-first services under `src/services`
- Current model services under `src/models` and `src/services`

## Bottom Line

The app is safer and more inspectable than before, but it is **not yet the full research-compliant stats-first model**.

The current active app board is still based on `veteran_lve_v1_3_0`. The newer stats-first model exists as a preview/apply workflow (`veteran_lve_stats_first_v1_0_0`), with fixtures and guardrails, but it has not replaced the active board. That is the biggest practical reason the app can still show rankings that violate the newest research expectations.

The implementation currently has good scaffolding:

- review-only trust status
- identity review scaffolding
- source coverage and warning infrastructure
- model receipts/contributions
- preview/apply boundary for stats-first outputs
- named sanity fixtures for Kyren/Bijan/Gibbs/Jeanty, JSN/Tee, BTJ/Luther, Chase Brown/Luther
- draft UX improvements

But the backbone data layer required by the reports is still partial:

- no actual nflverse/ffverse fetch or import adapter yet
- no canonical `gsis_id` warehouse model yet
- no play-by-play validation layer
- no expected opportunity ingestion from `load_ff_opportunity`
- no `ff_playerids`, `players`, or weekly roster import
- no percentile normalization from 2018-2025 qualified seasons
- no empirical-Bayes shrinkage or winsorized training distributions
- no true VOR replacement baselines using `QB14`, `RB30`, `WR46`, `TE14`
- active pack rankings still come from the older model output format

## Active Pack Reality Check

The active pack at `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv` has:

- `model_version = veteran_lve_v1_3_0`
- columns like `private_score`, `market_score`, `war_score`, `keeper_score`, `drop_candidate_score`
- no `private_lve_value`
- no `win_now_value`
- no `dynasty_hold_value`
- no `market_edge_score`
- no stats-first feature contribution columns

That means the visible app is not yet using the report's final stats-first output contract.

Current suspicious active-pack examples:

| player | active visible issue |
|---|---|
| Kyren Williams | Active pack ranks him above Bijan/Gibbs/Jeanty by keeper score, which the new sanity fixtures explicitly reject. |
| JSN vs Tee Higgins | Active pack has Tee above JSN by keeper score, which the new stats-first sanity fixtures reject. |
| Luther Burden vs BTJ/Chase Brown | Active pack still reflects older mixed logic; the new sanity fixtures require proven NFL production to show clearly in receipts. |

This is not just a UI problem. The active pack needs to be regenerated or replaced after the data and model gates pass.

## Coverage By Requirement Area

| area | report requirement | current app status | notes |
|---|---|---|---|
| Review-only safety | Rankings stay review-only until calibration/identity/source gates pass. | Mostly done | `model_recalibration_service`, trust status, data pack health, freeze guardrails, and tests exist. |
| Raw nflverse imports | Import weekly stats, PBP, players, weekly rosters, `ff_playerids`, snap counts, `ff_opportunity`. | Partial / mostly missing | Templates/validators exist for a small subset, but no actual dataset adapter/fetcher and several required datasets are absent. |
| Raw CSV contract | Persist `dim_player_ids`, `dim_players`, `fact_player_week_stats`, `fact_player_week_usage`, `fact_player_week_health`, `fact_player_week_xfp`. | Not implemented | Current templates use `nflverse_player_stats_weekly.csv`, `nflverse_snap_counts_weekly.csv`, etc. This is a simpler prototype contract, not the report contract. |
| Identity bridge | Use `gsis_id` as canonical key; Sleeper as crosswalk; block ambiguous matches. | Partial | `nflverse_identity_service.py` validates maps and review status, but local `player_id` remains the primary key in many places. No `ff_playerids` ingestion yet. |
| Local LVE actual scoring | Compute LVE points from component stats. | Partial | `lve_scoring_derivation_service.py` computes actual points from weekly stats. Constants are hardcoded, not configurable. No PBP validation yet. |
| Expected LVE scoring | Compute expected LVE from expected component stats, not generic xFP. | Not really implemented | `lve_opportunity_weekly.csv` template exists, but normalization currently uses projection import as `expected_lve_points_score`. No `load_ff_opportunity` adapter. |
| First-down logic | Import/derive rushing and receiving first downs; validate with PBP. | Partial | Weekly scoring uses rushing/receiving first-down columns if present. PBP validation and expected first-down derivation are missing. |
| Role/usage | Build snap/share/route/target/security features; mark proxies as caveated. | Partial | Role service uses snap counts, participation proxies, depth chart proxy. It does not have true route denominators; proxy caveats need to be more visible in receipts/gates. |
| Injury durability | Use historical injuries/status, lower-body rules, games missed; avoid fake certainty. | Partial | Injury service exists and handles lower-body risk, recurrence, availability, practice status. Report says current nflverse injuries may not cover 2025+, so current injury gaps must cap/degrade rather than block/invent. |
| Normalization | Three-year recency blend, active-game rates, shrinkage, winsorization, percentile training distributions. | Missing / prototype only | `lve_normalization_service.py` uses simple fixed anchors and a neutral `age_curve = 50.0`. This is not the report's normalization engine. |
| Feature buckets | Build H, X, R, E, F, EFF, P, A, D, M, VOR buckets. | Not implemented | Current feature buckets are `production`, `opportunity`, `role`, `efficiency`, `first_down_td_fit`, `age_window`, `injury_durability`. |
| Replacement baselines / VOR | Use `QB14`, `RB30`, `WR46`, `TE14` and projected LVE PPG above replacement. | Missing | Current stats-first service uses score baselines like QB 76 / RB 72 / WR 72 / TE 69. |
| Market isolation | Market contributes 0% to private/stat value; only trade/liquidity/edge. | Mostly done in stats-first path | `market_influence_policy_service.py` sets private/stat market weight to `0.0`. Stats-first tests verify private value ignores market. Active pack still exposes older `market_score/war_score` labels. |
| League rank handling | League rank is forced-release/rule context, not player quality. | Partial | Current app has league-rank pressure logic. Need continue auditing places where league rank indirectly moves keeper/drop recommendation. |
| Stats-first formula | Build private, win-now, dynasty-hold, keeper, drop, trade, confidence. | Partial / substantial | `lve_stats_first_veteran_formula_service.py` exists and has position-specific logic, but it does not match the final report's bucket/VOR/normalization contract. It is best treated as a preview prototype. |
| Sanity fixtures | Kyren/Bijan/Gibbs/Jeanty, JSN/Tee, BTJ/Luther, Chase Brown/Luther, QB/TE suppression. | Partially done | Tests exist in `tests/test_lve_stats_first_veteran_formula_service.py`. Active pack still fails some of these examples because active pack is old model output. |
| Calibration/backtest | Rolling backtest, train 2018-2023, validate 2024, test 2025. | Missing / fixture-only | Current calibration service is scenario/fixture-based, not a true historical replay across nflverse seasons. |
| UI receipts/compare | Show raw values, normalized scores, weights, contributions, source, warnings. | Partial | Receipt and compare services exist. They need to be wired to final bucket model and active outputs once stats-first path becomes authoritative. |
| Preview/apply workflow | Raw import and preview do not mutate active pack; apply requires explicit confirmation. | Mostly done | `lve_stats_first_preview_service.py` and `lve_stats_first_apply_service.py` enforce preview/apply boundaries. |

## Current Architecture Mismatch

The reports describe a real local analytics warehouse:

```text
nflverse/ffverse source snapshots
  -> raw dim/fact CSVs
  -> locally derived LVE actual/expected scoring
  -> recency/shrinkage/percentile normalized player inputs
  -> bucket scores
  -> model outputs
  -> preview/apply gate
```

The app currently has more of a prototype bridge:

```text
manual/template CSVs
  -> simple derived weekly scoring / role / injury / projection rows
  -> anchor-based normalized feature rows
  -> stats-first preview outputs
  -> optional applied pack
```

That prototype is useful, but it is not enough to trust the rankings for money decisions.

## Specific Gaps That Matter Most

### 1. Active board still uses old model

The active pack is `veteran_lve_v1_3_0`, not `veteran_lve_stats_first_v1_0_0`.

This means current visible rankings are not the latest stats-first prototype, and definitely not the final report model.

### 2. The app has templates, not real nflverse adapters

`nflverse_raw_import_service.py` validates local CSV headers. It does not download or convert:

- `load_player_stats`
- `load_pbp`
- `load_players`
- `load_rosters_weekly`
- `load_ff_playerids`
- `load_snap_counts`
- `load_ff_opportunity`

So the model cannot yet rebuild trusted stats from public nflverse sources automatically.

### 3. Normalization is not research-grade yet

Current normalization uses fixed anchors like position PPG anchors and first-down anchors. The reports require:

- three-year recency weighting
- active-game rate features
- empirical-Bayes shrinkage
- 2018-2025 training distributions
- winsorization
- percentile normalization by position

That work is still missing.

### 4. Expected opportunity is not wired correctly

The reports want expected LVE points from expected component stats. The current service mostly uses projections as `expected_lve_points_score`. That is useful, but it is not the same as expected opportunity from nflverse/ffverse.

### 5. Replacement baselines are not true VOR

The reports specify:

- `QB14`
- `RB30`
- `WR46`
- `TE14`

The current stats-first service uses score baselines, not projected LVE PPG replacement lines. This can distort cross-position ordering.

### 6. Age curve is still a placeholder in normalized features

`lve_normalization_service.py` sets `age_curve = 50.0`. For veterans, this is a major trust gap, especially RBs.

### 7. Current active output labels are still muddy

The active pack exposes:

- `private_score`
- `market_score`
- `war_score`
- `keeper_score`

The reports imply clearer labels:

- stats value / private LVE value
- market/trade liquidity
- market edge
- keep priority
- cut risk
- confidence / warning

The Draft UX and recent page cleanup improved this, but the active data columns still reflect older wording.

## What Is Good And Should Stay

Keep these pieces:

- Review-only trust gate.
- Preview-only stats-first output generation.
- Explicit apply workflow.
- Market influence lock for stats-first private value.
- Named sanity tests.
- Player receipts/contribution rows.
- Player compare tooling.
- Draft Board / Rankings split.
- Source coverage and warning infrastructure.
- Identity map validator.

These are the right safety rails. The problem is the data/model backbone underneath them is not finished.

## Decisions Needed Before More Coding

These are the places where the research and app need one clear policy before implementation:

| decision | why it matters |
|---|---|
| Keep current prototype CSV names or migrate to report `dim_*` / `fact_*` tables? | Migration is cleaner long-term; adapters are faster short-term. |
| Python direct downloads vs R-assisted nflreadr export? | nflverse is R-native in places; Python can use remote files but may need exact URLs/parquet/RDS handling. |
| How to handle current injury gaps? | Report says nflverse injury data may be historical-only; app should not block all model use because no current injury feed exists. |
| Are the report sanity fixtures hard ordering gates or review flags? | Some fixtures should be hard gates, but over-hardcoding player names can create fake confidence. |
| Should `keeper_score` include the tiny market nudge? | Stats-first private value is market-free, but keeper currently has a small market nudge. This may be acceptable as display/action context, but it should be explicitly labeled. |

## Recommended Next Implementation Order

1. Stop treating the active `veteran_lve_v1_3_0` pack as a final model. Keep it review-only.
2. Build true nflverse/ffverse source adapters or a documented local export command path.
3. Add the report raw tables: `dim_player_ids`, `dim_players`, `fact_player_week_stats`, `fact_player_week_usage`, `fact_player_week_health`, `fact_player_week_xfp`.
4. Make `gsis_id` the canonical stats key and map Sleeper IDs through `ff_playerids`.
5. Compute actual and expected LVE points from component fields.
6. Build source coverage gates per player.
7. Build the percentile normalization engine from 2018-2025 player-seasons.
8. Add H/X/R/E/F/EFF/P/A/D/M/VOR bucket outputs.
9. Rewrite stats-first formulas to consume bucket scores instead of prototype features.
10. Run named sanity fixtures and true historical backtests.
11. Generate a stats-first preview.
12. Compare active vs preview in Model Lab.
13. Apply only after identity, source coverage, sanity, and calibration gates pass.

## Current Trust Verdict

Current app infrastructure: **useful and improving**

Current active rankings: **not money-decision ready**

Current stats-first prototype: **promising, but not final**

Main blocker: **the app has safety rails and prototype formulas, but it does not yet have the full public-data ingestion, normalization, VOR, and calibration system required by the reports.**
