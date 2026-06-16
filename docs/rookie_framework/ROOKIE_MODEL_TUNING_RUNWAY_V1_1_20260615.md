# Rookie Model Tuning Runway v1.1

Date: 2026-06-15

Lane: Rookie framework only

## Executive Verdict

Verdict: YELLOW

The v1.1 tuning runway ran on the repaired 2010-2023 complete-window historical pool with the required split discipline:

- Train: 2010-2019
- Development validation: 2020-2021
- Final validation: 2022-2023
- 2024-2025: excluded from tuning
- 2026: not used for tuning

No v2 candidate board was created. The tested candidate configurations did not clear validation and stability strongly enough to justify a new manual-use board. The safest result is to keep the current CFBD-enriched baseline as the reference and use the v1.1 outputs as tuning diagnostics only.

Production implementation remains blocked. No production rankings, private scores, app wiring, probabilities, bands, hidden sort keys, Outcome HQ files, or veteran files were changed.

## Files Inspected

- `local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/expanded_historical_labels_v2_20260615.csv`
- `local_exports/rookie_framework/cfbd_identity_join_repair_20260615/cfbd_drafted_rookie_feature_join_repaired_20260615.csv`
- `local_exports/rookie_framework/draft_ranking_model_v1_20260615/rookie_draft_ranking_v1_20260615.csv`
- `scripts/rookie_framework/audit_rookie_cfbd_enriched_baseline_runway_v1.py`
- `docs/rookie_framework/ROOKIE_CFBD_ENRICHED_TUNING_CANDIDATE_AUDIT_20260615.md`

## Files Created

- `scripts/rookie_framework/tune_rookie_model_runway_v1_1.py`
- `tests/test_rookie_model_tuning_runway_v1_1.py`
- `docs/rookie_framework/ROOKIE_MODEL_TUNING_RUNWAY_V1_1_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/model_tuning_runway_v1_1_20260615/`:

- `candidate_configurations_v1_1_20260615.csv`
- `candidate_validation_metrics_v1_1_20260615.csv`
- `candidate_year_class_metrics_v1_1_20260615.csv`
- `candidate_position_metrics_v1_1_20260615.csv`
- `candidate_wr_signal_metrics_v1_1_20260615.csv`
- `feature_ablation_metrics_v1_1_20260615.csv`
- `candidate_star_bust_frontier_v1_1_20260615.csv`
- `candidate_decision_v1_1_20260615.csv`
- `top_missed_stars_after_tuning_v1_1_20260615.csv`
- `high_ranked_busts_after_tuning_v1_1_20260615.csv`
- `README_ROOKIE_MODEL_TUNING_RUNWAY_V1_1_20260615.md`

These exports are local-only and not committed.

## Candidate Configurations Tested

- `scoring_format_fit_plus_v2`
- `wr_star_capture_plus`
- `cfbd_market_share_plus`
- `draft_capital_trap_guard`
- `balanced_star_bust_frontier`
- `position_calibrated_v2`
- `ensemble_rank_blend_v1`

Baseline reference:

- `cfbd_enriched_baseline_v1_1`

All candidate changes were general feature-family weight/gate changes. No candidate used player names, player IDs, school, NFL team, exact class, or known outcomes as scoring features.

## Baseline Metrics

Reference candidate: `cfbd_enriched_baseline_v1_1`

Development validation, 2020-2021:

| Bucket | Stars Captured | Star Capture | Bust Rate |
|---|---:|---:|---:|
| Top 12 | 12 / 19 | 0.632 | 0.250 |
| Top 24 | 14 / 19 | 0.737 | 0.396 |
| Top 36 | 17 / 19 | 0.895 | 0.528 |

Final validation, 2022-2023:

| Bucket | Stars Captured | Star Capture | Bust Rate |
|---|---:|---:|---:|
| Top 12 | 6 / 16 | 0.375 | 0.292 |
| Top 24 | 11 / 16 | 0.688 | 0.396 |
| Top 36 | 12 / 16 | 0.750 | 0.514 |

## Best Candidate Decision

Best gated result: `cfbd_enriched_baseline_v1_1`

No challenger cleared the full validation/stability gate. Several candidates improved final Top 36 star capture, but they either lost development validation stability, increased final Top 12 bust exposure, failed to improve WR-specific capture, or did not improve the key Top 24 bucket.

Selected candidate decision: no new v2 candidate board.

## Candidate Highlights

`scoring_format_fit_plus_v2`:

- Final Top 24 star capture matched baseline at 0.688.
- Final Top 36 star capture improved from 0.750 to 0.812.
- Development Top 24 star capture fell by 0.053.
- Final Top 12 star capture fell by 0.063.
- Final Top 12 bust rate increased by 0.125.
- Decision: fail candidate gate.

`wr_star_capture_plus`:

- Final Top 24 star capture matched baseline at 0.688.
- Final Top 36 star capture fell by 0.062.
- Development Top 24 star capture fell by 0.105.
- WR final Top 24 star capture did not improve.
- Decision: fail candidate gate.

`balanced_star_bust_frontier`:

- Final Top 36 star capture improved by 0.062.
- Final Top 24 bust rate improved by 0.042.
- Development Top 24 star capture fell by 0.053.
- Final Top 12 star capture fell by 0.063.
- Decision: fail candidate gate.

`ensemble_rank_blend_v1`:

- Final Top 36 star capture improved by 0.062.
- Final Top 24 bust rate improved by 0.042.
- Development Top 24 bust rate improved by 0.042.
- Final Top 12 bust rate increased by 0.042 and no key Top 24 star capture gain appeared.
- Decision: fail candidate gate with YELLOW stability.

## WR Signal Review

Final validation WR Top 24:

| Candidate | Stars Captured | Star Capture | Bust Rate |
|---|---:|---:|---:|
| `cfbd_enriched_baseline_v1_1` | 3 / 4 | 0.750 | 0.375 |
| `scoring_format_fit_plus_v2` | 3 / 4 | 0.750 | 0.417 |
| `wr_star_capture_plus` | 3 / 4 | 0.750 | 0.417 |
| `cfbd_market_share_plus` | 3 / 4 | 0.750 | 0.417 |
| `balanced_star_bust_frontier` | 3 / 4 | 0.750 | 0.417 |

The WR-upside configurations did not improve final validation WR star capture and generally increased WR bust exposure in the Top 24 slice. That blocks a v2 board under the v1.1 stability standard.

## Position Calibration Snapshot

Baseline Top 24 by position over the full 2010-2023 complete-window pool:

| Position | Stars Captured | Star Capture | Bust Rate |
|---|---:|---:|---:|
| QB | 8 / 17 | 0.471 | 0.083 |
| RB | 17 / 46 | 0.370 | 0.000 |
| WR | 9 / 37 | 0.243 | 0.125 |
| TE | 11 / 25 | 0.440 | 0.042 |

WR remains the biggest model-quality gap. The current local features help but do not yet create a stable WR star-capture gain.

## Feature Ablation Findings

Final validation Top 24:

| Ablation | Star Capture | Bust Rate | Interpretation |
|---|---:|---:|---|
| Draft capital + position only | 0.625 | 0.417 | Draft/position is useful but weaker than the enriched baseline. |
| CFBD production only | 0.438 | 0.542 | Production alone is not enough and raises bust exposure. |
| CFBD market share only | 0.438 | 0.625 | Share alone is too noisy for this pool. |
| Scoring-format fit only | 0.625 | 0.583 | Fit helps identify some players but is unsafe alone. |
| CFBD production + market share | 0.438 | 0.583 | Combined CFBD-only signal is not stable enough without draft/position context. |
| Draft + CFBD production/market share | 0.625 | 0.438 | Better than CFBD-only, but still below the enriched baseline. |

The ablations support keeping draft/position context, using CFBD as controlled context, and avoiding a heavy market-share-only WR push.

## Anti-Cheat / Leakage Audit

- PASS: `player_name`, aliases, player IDs, schools, teams, and draft classes were not used as direct scoring/tuning features.
- PASS: Names appear only in diagnostics for missed stars and high-ranked busts.
- PASS: Outcome labels were used only for evaluation metrics.
- PASS: No ADP, market, public ranking, projection, consensus, trade value, or draft-kit rank fields were used as private score inputs.
- PASS: No player-specific boosts or penalties were added.
- PASS: Tuning changes were feature-family/weight/gate changes only.
- PASS: 2024-2025 partial-window rows were excluded from tuning.
- PASS: 2026 rows were not used for tuning.
- PASS: No probabilities, bands, hidden sort keys, or app-readable outputs were created.

## V2 Candidate Board Decision

V2 candidate board created: no

Reason: no candidate cleared validation and stability strongly enough. The current safest state is diagnostic exports only. Creating a v2 manual-use board now would risk overfitting a small final-validation gain and would not resolve the WR capture concern.

## Manual Draft Trust

Manual draft trust verdict: YELLOW

The analyzer remains useful as a manual advisory board with visible warnings and human review, but it should not be treated as a production ranking or as a fully tuned draft board. It can help Tim identify candidate groups, warnings, and historical signal weaknesses. It should not be used to blindly draft from top to bottom.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -8`
- `git diff --check`
- `python -m py_compile scripts\rookie_framework\tune_rookie_model_runway_v1_1.py tests\test_rookie_model_tuning_runway_v1_1.py`
- `python scripts\rookie_framework\tune_rookie_model_runway_v1_1.py`
- `python tests\test_rookie_model_tuning_runway_v1_1.py`
- `python scripts\rookie_framework\build_rookie_review_board_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_shadow_ranking_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_production_candidate_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_analyzer_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_day_simulation_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_ranking_v01.py`
- `python scripts\rookie_framework\build_rookie_historical_outcome_labels_v1.py`
- `python scripts\rookie_framework\backtest_rookie_ranking_model_v01.py`
- `python scripts\rookie_framework\build_rookie_historical_allowlist_qa_expanded_baseline_v1.py`
- `python scripts\rookie_framework\build_rookie_cfbd_historical_feature_cache_v1.py --skip-fetch`
- `python scripts\rookie_framework\audit_rookie_cfbd_identity_join_repair_v1.py`
- `python tests\test_rookie_cfbd_enriched_baseline_runway_v1.py`
- `python tests\test_rookie_cfbd_identity_join_repair_v1.py`
- `python tests\test_rookie_cfbd_historical_feature_cache_v1.py`
- `python tests\test_rookie_historical_allowlist_qa_expanded_baseline_v1.py`
- `python tests\test_rookie_experimental_tuning_candidate_v1.py`
- `python tests\test_rookie_backtest_framework_v01.py`
- `python -m pytest tests\test_rookie_model_tuning_runway_v1_1.py -q`
- `Select-String -Path scripts\rookie_framework\tune_rookie_model_runway_v1_1.py -Pattern 'api_key|CFBD_API|if\s+.*player|player_name\s*==|private_score|probability|band|streamlit|outcome_probability' -CaseSensitive:$false`

Pytest was unavailable: `No module named pytest`. Direct harnesses passed.

## Remaining Risks

- WR historical star capture remains weak and unstable.
- CFBD market-share-only and production-only signals are too noisy without draft/position context.
- Some candidate improvements appear in Top 36 but do not improve Top 24 enough for draft-day confidence.
- Current 2026 application should stay manual/review-only until a future candidate clears stability gates.

## Recommended Next Step

Do not create a v2 board yet. The next rookie-only task should be a WR feature-quality improvement pass focused on source-safe, pre-draft information that can be applied historically and currently without leakage, followed by another split-stable tuning audit.
