# NWR Model Feature Opportunity Plan - 2026-06-23

Generated at UTC: 2026-06-24T02:39:20.128811+00:00

Scope: prioritization/spec only. This plan does not wire features into the model, retrain, mutate rankings, change app code, update latest pointers, update pinned snapshots, or touch Frozen Final Draft Board V1.

## Executive Verdict

**YELLOW.** NWR has a strong set of future model feature opportunities, but the best opportunities are not all formula tweaks. The highest-value work is source governance: recover true historical drop/draftable pools, repair identity coverage, prove scoring/as-of contracts, and only then test new features. Several tempting features must remain diagnostic or display-only until source timing, licensing, and missingness are solved.

## Priority Themes

### P0: Build The Foundation Before Tuning

1. **Verified historical dropped-veteran truth panel**: needed before real rookie-veteran calibration. Current 2010-2021 rows are proxy-only, 2022-2024 inferred, and 2026 current context.
2. **Verified historical draftable/free-agent pool**: required to avoid backtests pretending missing veteran history is empty.
3. **League scoring and roster-construction contract**: 10-team 1QB, non-PPR, first-down scoring, K de-emphasis must be encoded per season before backtesting.
4. **Player identity join coverage**: player_id gaps and name+position fallback are a P0 reliability risk.
5. **Current injury/news/role status**: urgent for draft trust, but safest first as diagnostic/confidence context, not hidden value.

### P1: Best Safe Model Inputs After Gates

- Age and age curve by position.
- Multi-year production trend using prior completed seasons only.
- Games played/missed time and per-game versus annual-total splits.
- First-down scoring fit and non-PPR scoring fit.
- QB de-emphasis for 1QB format.
- TE no-premium scarcity/volatility context.
- RB cliff/workload risk.
- WR target earning and efficiency.
- Rookie college production after identity gate.
- Completed NFL Draft capital, separated from pre-draft mock/big-board fields.
- Roster construction scarcity after as-of roster verification.

### P2/P3: Useful But Gated

- RotoWire/PFF route, TPRR, YPRR, red-zone, yards-after-contact, or charting fields: useful only after license/source admission and rank/projection quarantine.
- Future pick value context: decision support first, not player value.
- Market sanity gap: display-only diagnostic, never NWR value.
- FantasyPros ADP/ECR/projections, external analyst ranks, PFF grades/big boards: banned as model inputs.

## Feature Classification Rules

- `model_input_after_gate`: may be tested only after timing, source, identity, leakage, missingness, and license checks.
- `diagnostic_only`: may affect caveats, confidence, review queues, or manual checks first; not private value without later approval.
- `display_only`: may appear in reports/app props as context but must never become hidden sort, rank, or private value.
- `sensitivity_only`: used only for robustness/gap analysis, never training truth or source-truth labels.
- `identity_only`: can improve joins but not player value.
- `banned`: blocked from model input.

## Top P0/P1 Opportunities

| Feature | Use Class | Why It Matters | First Safe Test |
| --- | --- | --- | --- |
| verified historical drop truth panel | model_input_after_gate | Enables real rookie-veteran availability cohorts. | Row eligibility audit with ACTUAL/HIGH only. |
| verified draftable pool history | model_input_after_gate | Prevents empty-pool backtest bias. | Season manifest with source_class/confidence counts. |
| scoring/roster construction fit | model_input_after_gate | Aligns to LVE 1QB, non-PPR, first-down rules. | Scoring contract audit by season. |
| identity join coverage | identity_only | Reduces wrong-player joins. | Exact/fuzzy/unmatched join audit. |
| age and position curves | model_input_after_gate | Improves RB/WR/TE/QB lifecycle handling. | Coverage report by source and position. |
| first-down and non-PPR fit | model_input_after_gate | Directly models LVE scoring differences. | Prior-season scoring reconstruction. |
| multi-year production trend | model_input_after_gate | Separates trend from one-year noise. | Prior-3-year trend with as-of dates. |
| games/missed time | model_input_after_gate | Separates per-game talent from availability risk. | Per-game vs annual-total audit. |
| WR target earning / opportunity share | model_input_after_gate | Better role signal than raw yards. | Prior-season target/share audit. |
| rookie college production + draft capital | model_input_after_gate | Strong rookie priors if as-of safe. | CFBD identity/coverage audit and post-draft mode split. |

## Features That Must Stay Display-Only Or Diagnostic

- DynastyProcess values/ECR, ADP, FantasyPros ranks/projections, trade calculators, and market ranks: display-only or banned.
- Outcome probability/display columns: display-only until a release gate explicitly admits them for a model target; missing means `Not enough information`, not zero.
- Future pick value context: diagnostic/trade-support first.
- Current injury/news/role status: diagnostic/confidence first until source coverage is stable.
- Local source-risk heatmap and warning flags: diagnostic/display for trust, not hidden sort.

## Features Blocked By Missing Data

- True historical dropped-veteran panel.
- Full verified historical free-agent/draftable pool.
- Current injury/news/role automation.
- Complete rookie ages/DOB.
- Complete player_id coverage for frozen board/PDF rows.
- Historical trade and future pick ownership history.
- Complete route/snap/participation coverage by season.
- Licensed factual vendor usage fields.

## Recommended First Safe Tests

1. **Identity and row eligibility audit**: verify every candidate row has player identity, source_class, confidence, source date, and allowed use.
2. **Scoring contract audit**: rebuild LVE non-PPR/first-down points from raw stats for prior completed seasons.
3. **Missingness report**: quantify feature coverage by position, season, and source before scoring.
4. **No-market blocked-field scan**: assert no ADP/ECR/market/projection/rank tokens enter model input candidates.
5. **Dry-run feature report**: produce candidate feature distributions and caveats only, no rank or model output changes.

## Guardrails For Any Future Implementation

- Do not use `PROXY_DROP`, `PROXY_ONLY`, or `LOW` confidence rows as training truth.
- Do not convert market/ADP/display context into NWR value.
- Do not treat missing data as low value or clean absence of risk.
- Do not use current 2026 facts as historical as-of features.
- Do not use post-draft facts in pre-draft rookie mode.
- Do not use external ranks, projections, grades, or big boards as model features.

## Inventory

The companion CSV `NWR_MODEL_FEATURE_CANDIDATE_INVENTORY_20260623.csv` contains row-level feature candidates, source status, use classification, priority, leakage/missingness risk, implementation difficulty, and first safe test.

## Non-Goals

- No app change.
- No model code change.
- No retraining.
- No ranking mutation.
- No raw vendor data tracking.
- No shared-data tracking.
- No latest pointer, pinned snapshot, or frozen board mutation.
