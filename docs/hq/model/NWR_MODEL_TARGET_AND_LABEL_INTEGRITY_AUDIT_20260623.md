# NWR Model Target And Label Integrity Audit - 2026-06-23

Generated at UTC: 2026-06-24T02:34:10.900012+00:00

Scope: model accountability only. This audit does not change app code, model/rank logic, latest pointers, pinned snapshots, frozen board artifacts, source-truth data, or training behavior.

## Executive Verdict

**YELLOW.** NWR has strong guardrails and several clear actual outcome labels for backtesting, but the current ecosystem mixes deterministic review scores, display-only probabilities, current availability context, inferred drops, and proxy cohorts. The main risk is not that the repo lacks warnings; the risk is that a future tuning pass could accidentally treat review/proxy/display rows as supervised truth.

## Current Model Outputs

1. **Veteran/current value outputs**: `veteran_base_value`, `nwr_dynasty_score`, `keeper_score`, `drop_candidate_score`, `trade_value`, `confidence_score`, warning/risk flags, and legacy recommendations. These are deterministic formula outputs, not observed truth labels.
2. **Rookie outputs**: `final_decision_score`, `board_rank`, `recommended_range_label`, `do_not_draft_before_pick`, confidence/missingness/risk flags. These are formula outputs and manual-use/review outputs, not observed truth labels.
3. **Backtest labels**: `next_nwr_points`, `next_nwr_ppg`, and position finish flags such as `qb_t12`, `rb_t24`, `wr_t36`, `te_t12`. These are actual future outcome labels when built from finalized season stats and paired only with as-of-safe features.
4. **Rookie historical outcome labels**: `best_3yr_ppg`, `starter_level_seasons`, `outcome_label`, `hit_label`, `top24_seasons`. These can be actual labels when mature and source-approved; partial/too-early/not-loaded rows require filtering.
5. **Outcome Columns props**: QB/RB/WR/TE top-finish display columns. These are display-only and must not override rank, sort, or private value.
6. **Frozen Final Draft Board V1**: approved draft-day baseline rank/tier/visible score/availability. It is source truth for display, not an observed performance label.
7. **Drop Decision/historical drop outputs**: 2025/2026 actual or current availability context, 2022-2024 inferred PDF rows, 2010-2021 proxy rows. These are not value labels and not bad-cut proof.
8. **Cross-asset tuned candidate overlay**: review-only candidate ranking/value derived from incomplete historical and proxy evidence. Not training truth and not approved rank.
9. **Market/ADP/display context**: price/liquidity/timing context only. Never private value, hidden sort, training target, or rank driver.

## Label Inventory

See `NWR_MODEL_LABEL_INVENTORY_20260623.csv` in this folder for row-level classification.

## Training Label Classification

### Labels Safe For Training, With Conditions

- `next_nwr_points`, `next_nwr_ppg`, and top-finish flags from Backtest V0/V1 are valid future outcome labels when every feature row is as-of safe and blocked-field scans pass.
- Mature rookie future outcome labels such as `best_3yr_ppg`, `starter_level_seasons`, and mature `outcome_label` are valid only when the source/license policy is approved and the feature snapshot predates the draft decision.
- League-state facts such as rostered/free-agent/available/pick ownership are valid for league-state or availability tasks only, with timestamps. They are not value/outcome labels.

### Labels Not Safe For Training

- `PROXY_DROP`, `PROXY_ONLY`, and `LOW` confidence rows.
- 2010-2021 proxy dropped-veteran rows.
- 2022-2024 inferred/unprotected PDF rows unless upgraded by transaction/commissioner evidence; even then, they are availability labels, not value labels.
- 2026 dropped-veteran package rows as bad-cut or future outcome truth; they are current availability/unprotected context.
- Outcome Columns display percentages.
- Market/ADP/DynastyProcess/FantasyPros values, ranks, ECR, projections, or market edge.
- Frozen board rank as outcome truth.
- Rookie/veteran formula scores, candidate overlays, manual-review flags, and legacy recommendations.

## Source Truth Inputs

- Frozen Final Draft Board V1 for draft-day display baseline and availability context.
- Sleeper league state/rosters/picks/transactions after a fresh pull and with source timestamp.
- Explicit PDF `CUT` rows for 2025 as cut-list evidence, not performance truth.
- Approved Drop Decision 2026 dropped-veterans package for local-live-test availability validation.
- Finalized season stats used to build future outcome labels.

## Inferred Inputs

- 2022-2024 LVE cut-list/unprotected PDF rows in the historical reconstruction.
- Manual-review flags and warning bands inferred from evidence coverage, caveats, and source status.
- Cross-asset review overlay adjustments where no clean historical rookie-veteran panel exists.

## Proxy / Sensitivity-Only Inputs

- 2010-2021 historical dropped-veteran proxy rows.
- Historical cross-asset proxy cohorts.
- Proxy cut scores, archetypes, and synthetic prior-year proxy values.
- Any `PROXY_DROP`, `PROXY_ONLY`, or `LOW` confidence rows.

These may be used only for sensitivity testing, stress testing, simulation/backtest robustness checks, and gap analysis.

## Display-Only Inputs

- Outcome Columns props.
- ADP, ECR, market ranks, market values, DynastyProcess values, FantasyPros rank/projection-like fields.
- Trade helper props, decision-board risk cards, and app props that explicitly say decision support only.
- PDF ranks and other market/timing context unless separately admitted as factual source fields.

## Leakage Risks

1. **Future outcome labels leaking into features**: rookie outcome labels and backtest `next_nwr_*` labels are legitimate targets only after the prediction window.
2. **Final season aggregates used too early**: season-end stats are labels or prior-season features only, never current-season future knowledge.
3. **Current 2026 availability used as historical truth**: dropped-veteran package rows are current availability context, not historical bad-cut labels.
4. **Proxy rows promoted to truth**: proxy drop rows can fill shape gaps, but must never become direct training labels.
5. **Outcome display probabilities becoming value**: 12/66 matched rows means unsupported rows must remain `Not enough information`, not zero.
6. **Market/ADP/rank/projection columns becoming hidden features**: tests block obvious tokens, but local_exports rows still include display market columns that require discipline.
7. **Rookie post-draft fields in pre-draft runs**: registry fields marked `post_draft_only` must stay out of pre-draft scoring.

## Market / ADP Contamination Risks

Market contamination can happen when `market_rank`, `market_score`, `market_trade_value`, ADP, ECR, projection, or DynastyProcess value is treated as NWR private value. Current guardrails are good: market private/stat weights are 0.0, trade/market drift is capped, and backtest tests reject `adp`, `market`, `fantasy_points`, and similar blocked columns. The residual risk is human or future-script misuse of display columns from local exports.

## Missing Data Risks

- Missing Outcome rows can be misread as zero probability or low value; they must remain `Not enough information`.
- Rookie/veteran scoring can make missing numeric features look average if neutral defaults are viewed without the missing-data penalty and confidence cap.
- `needs_data`, `UNKNOWN`, missing team/status, missing player IDs, and unmatched PDF rows can look cleaner than they are in sorted tables.
- Proxy drop rows can hide the fact that true league history is still missing.

## Required Operating Rules

- Train only on actual future outcomes or timestamped league-state facts approved for the specific target.
- Keep all proxy/low-confidence rows sensitivity-only.
- Keep display-only fields out of rank/model/private value paths.
- Keep inferred rows separate and down-weighted until evidence upgrades them.
- Never treat dropped/available as proof of bad player value.
- Never treat missing data as zero, low value, or clean absence of risk.

## Files Inspected

Representative files inspected include:

- `MODEL_SPEC.md`, `DATA_MODEL.md`
- `src/models/veteran_scores.py`, `src/services/veteran_model_service.py`
- `src/models/rookie_scores.py`, `src/services/rookie_model_service.py`
- `src/services/model_v4_component_calculator_service.py`, `src/services/model_v4_formula_contract_service.py`
- `src/services/model_v4_rookie_outcome_label_service.py`
- `src/services/market_influence_policy_service.py`
- `src/services/legacy_label_quarantine_service.py`, `src/services/model_recalibration_service.py`
- `scripts/build_backtest_dataset_v0.py`, `scripts/build_backtest_dataset_v1.py`, `scripts/run_backtest_v0.py`, `scripts/run_backtest_v1.py`
- `tests/test_backtest_leakage_guards_v0.py`, `tests/test_backtest_feature_cleanup_v1.py`
- `docs/hq/parallel_lanes/NWR_BACKTEST_AS_OF_AND_LEAKAGE_RULES_V1.md`
- `docs/hq/data_sources/historical_drop_lists/*`
- `docs/hq/data_sources/NWR_PERSONAL_DATA_SOURCE_ACCOUNTABILITY_CATALOG_20260623.md`
- `docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns/*`
- `docs/hq/parallel_lanes/NWR_HISTORICAL_CROSS_ASSET_TUNING_20260622.md`
- `docs/hq/parallel_lanes/ROOKIE_HQ_FREEZE_AND_MOCK_DRAFT_HANDOFF_20260617.md`
