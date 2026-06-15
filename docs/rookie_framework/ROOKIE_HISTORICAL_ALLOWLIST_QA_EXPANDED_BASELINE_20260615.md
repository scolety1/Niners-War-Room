# Rookie Historical Allowlist QA + Expanded Baseline - 2026-06-15

## 1. Executive Verdict

Verdict: GREEN for local-only allowlist QA, expanded historical labels v2, and expanded baseline scaffolding.

This pass completed the four approved steps:

1. Draft-source allowlist/quarantine audit.
2. Assumed-zero/no-stat alias-ID QA for the 135 previously suspected rows.
3. Expanded historical labels v2 for 2010-2023 complete-window backtest rows, with 2024-2025 retained as partial-window report-only rows.
4. Expanded baseline evaluation after the label/join gates passed.

This did not tune the rookie ranking model, did not create a v2 current rookie board, did not promote artifacts, did not create probabilities or bands, and did not touch app, Streamlit, Outcome, veteran, private-score, or production-ranking files.

## 2. Source Discovery and Allowlist

Inputs inspected:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/nflverse_draft_picks.csv`
- `local_exports/rookie_framework/historical_outcome_labels_v1_20260615/rookie_historical_outcome_labels_v1_20260615.csv`
- `local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/historical_rookie_backtest_feature_matrix.csv`

Draft-source allowlist audit result:

- Total draft-source columns audited: 36
- Allowed identity/display columns: 11
- Allowed draft-capital feature columns: 2 (`round`, `pick`)
- Quarantined future/career columns: 23
- Ambiguous unrecognized columns: 0

Allowed scoring/baseline inputs from the draft source are limited to draft capital (`round`, `pick`) and position. Identity fields are retained only for display, joins, grouping, and QA diagnosis. Career/future fields such as `w_av`, `car_av`, `dr_av`, `games`, `allpro`, `probowls`, and career stat totals remain quarantined.

## 3. Assumed-Zero QA

The 135 assumed-zero/no-stat rows were rechecked against local raw stat evidence and identity fields.

QA classifications:

- `true_zero_no_nfl_fantasy_stats`: 96
- `id_repaired`: 10
- `position_mismatch_repaired`: 19
- `stat_source_coverage_gap`: 10

Repair/export results:

- Alias/ID repair action rows: 29
- Excluded rows pending manual review: 10
- Backtest-ready rows after QA: 1,099

Important repair note:

- Some local stat rows have valid player IDs but blank position fields. The builder now handles this with a generic identity-only repair: if `gsis_id` matches a draft row and the stat position is blank/missing, the draft identity position is used to recover the stat row. This is not player-specific tuning and does not use labels or outcomes as features.

Remaining non-ready cases are source-coverage gaps where later stat rows exist outside the first-three-year rookie outcome window. Those rows are excluded from backtest-ready evaluation pending manual review rather than silently treated as valid zero-label rows.

## 4. Expanded Label Pool

Expanded labels v2 output:

- Total rows: 1,269
- 2010-2020 expanded rows: 874
- 2021-2025 carried-forward v1 rows: 395
- Complete-window non-partial rows: 1,109
- Backtest-ready rows: 1,099
- Partial-window/report-only rows: 160
- Excluded rows: 10
- Duplicate label keys checked: 0 duplicate player/year/position/pick keys found

Label status counts:

- `GREEN_COMPLETE`: 1,003
- `YELLOW_ASSUMED_ZERO`: 96
- `YELLOW_PARTIAL_WINDOW`: 160
- `EXCLUDED`: 10

Position counts:

- WR: 499
- RB: 346
- TE: 240
- QB: 184

The labels reconstruct Tim-scoring components from raw local stats where present. Return-yard scoring remains partial for pre-2025 rows because the inspected local stat source does not expose complete return-yard columns; this caveat is carried in `label_scoring_quality`.

## 5. Expanded Baseline

Expanded baseline verdict: GREEN as a local-only, no-tuning baseline.

The expanded baseline is a draft-capital/position baseline used to check label join feasibility and historical evaluation coverage. It is not the current rookie analyzer, not a tuned ranking model, and not a v2 draft board.

Overall complete-window metrics:

| Bucket | Rows | Stars Total | Stars Captured | Star Capture Rate | Bust Count | Bust Rate | Avg Three-Year Points |
|---|---:|---:|---:|---:|---:|---:|---:|
| Top 12 | 12 | 125 | 10 | 0.080 | 0 | 0.000 | 532.636 |
| Top 24 | 24 | 125 | 17 | 0.136 | 1 | 0.042 | 461.261 |
| Top 36 | 36 | 125 | 20 | 0.160 | 2 | 0.056 | 418.846 |

Diagnostic miss/bust output:

- Top misses and high-ranked bust rows exported: 107
- `missed_star`: 105
- `high_ranked_bust`: 2

The miss/bust file is diagnosis-only. It must not be used for player-specific rules or historical-result special casing.

## 6. Gate Results

Draft-source allowlist/quarantine: GREEN.

Assumed-zero/no-stat QA: GREEN with documented exclusions. All 135 rows were classified; 29 rows were repaired by identity/position evidence, 96 remained assumed-zero with caveat, and 10 were excluded pending manual review.

Expanded historical labels v2: GREEN for local-only evaluation/backtest inputs. Complete-window rows are separated from partial-window rows, and excluded rows are not backtest-ready.

Expanded baseline: GREEN for baseline evaluation only. No tuning was run.

Tuning readiness: RED. Tuning remains blocked until Tim/HQ explicitly approves a separate no-leakage tuning prompt.

## 7. Anti-Cheat / Leakage Audit

PASS - `player_name`, aliases, player IDs, school, NFL team, and draft year are used only for identity, display, grouping, joins, QA, and year splits. They are not direct scoring/tuning features.

PASS - Outcome labels are used only for evaluation and baseline metrics, never for feature construction.

PASS - ADP/market data is not used by this builder.

PASS - No player-specific boost/penalty logic was added.

PASS - No tuning changes were made.

PASS - Label/alias repair is separate from model tuning and is documented in `alias_id_repair_actions_20260615.csv`.

PASS - Expanded baseline runs on complete-window backtest-ready rows only. Partial 2024-2025 rows are excluded.

PASS - Top-miss/high-ranked-bust review is diagnosis-only and explicitly marked not for player-specific tuning.

## 8. Local-Only Exports

Created under `local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/`:

- `draft_source_allowlist_audit_20260615.csv`
- `assumed_zero_qa_20260615.csv`
- `alias_id_repair_actions_20260615.csv`
- `expanded_historical_labels_v2_20260615.csv`
- `expanded_baseline_results_20260615.csv`
- `expanded_baseline_year_position_summary_20260615.csv`
- `expanded_baseline_top_misses_and_busts_20260615.csv`
- `README_ROOKIE_HISTORICAL_ALLOWLIST_QA_EXPANDED_BASELINE_20260615.md`

These are local-only exports and are not committed.

## 9. Files Added

Tracked files added:

- `scripts/rookie_framework/build_rookie_historical_allowlist_qa_expanded_baseline_v1.py`
- `tests/test_rookie_historical_allowlist_qa_expanded_baseline_v1.py`
- `docs/rookie_framework/ROOKIE_HISTORICAL_ALLOWLIST_QA_EXPANDED_BASELINE_20260615.md`

## 10. Recommended Next Step

Pause before tuning.

The next rookie-only task should be a separate expanded-pool baseline audit / tuning-readiness decision prompt. That prompt should decide whether the 10 source-coverage exclusions and return-yard caveat are acceptable before any no-leakage tuning run is authorized.
