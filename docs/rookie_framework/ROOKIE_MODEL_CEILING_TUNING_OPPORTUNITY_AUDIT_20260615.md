# Rookie Model Ceiling / Historical Tuning Opportunity Audit

Date: 2026-06-16

Lane: Rookie framework only

## Executive Verdict

- More historical tuning worth doing: YELLOW
- Recommendation: narrow hypothesis only
- Broad tuning recommendation: do not broad-tune
- V2 board created: no
- Anti-cheat/leakage: PASS

The current best formula, `cfbd_enriched_baseline_v1_1`, appears near the practical ceiling for the available broad historical feature families. Rolling validation found a small top-36 signal for `draft_capital_trap_guard`, but no candidate consistently improved the premium windows where Tim's decisions matter most: top 12 and top 24.

The correct next move is not another broad sweep. Either freeze the current formula and rely on manual draft review, or run only a narrow, pre-registered hypothesis around a specific feature family such as WR/role-stability or source-coverage repair.

No tuning weights were changed. No v2 board, production ranking, private score change, app wiring, Streamlit file, Outcome file, veteran file, probability, band, hidden sort key, or promoted artifact was created.

## Files Created

- `scripts/rookie_framework/audit_rookie_model_ceiling_tuning_opportunity.py`
- `tests/test_rookie_model_ceiling_tuning_opportunity.py`
- `docs/rookie_framework/ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/model_ceiling_tuning_opportunity_audit_20260615/`:

- `rolling_validation_metrics_20260615.csv`
- `candidate_consistency_vs_baseline_20260615.csv`
- `strict_objective_diagnostics_20260615.csv`
- `feature_family_tuning_signal_20260615.csv`
- `manual_review_issue_diagnostics_20260615.csv`
- `model_ceiling_decision_20260615.csv`
- `anti_cheat_leakage_audit_20260615.csv`
- `README_ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md`

These exports are local-only and must not be committed.

## Current Model Ceiling Estimate

Estimated ceiling: moderate-high for available source-safe historical features.

The baseline captures many top-24/top-36 stars across the expanded pool, but it is less stable in the top 12 and in recent classes. That pattern suggests the model can structure the board well, but the remaining premium misses often require scouting, role, injury, depth-chart, or current-year context that is not fully captured by broad historical feature weights.

Baseline multi-year holdout summary:

| Holdout | Bucket | Star Capture | Bust Rate | WR Star Capture |
|---|---|---:|---:|---:|
| 2014-2016 | Top 12 | 0.522 | 0.028 | 0.667 |
| 2014-2016 | Top 24 | 0.783 | 0.125 | 0.889 |
| 2014-2016 | Top 36 | 0.826 | 0.148 | 0.889 |
| 2017-2019 | Top 12 | 0.455 | 0.028 | 0.333 |
| 2017-2019 | Top 24 | 0.727 | 0.042 | 0.667 |
| 2017-2019 | Top 36 | 0.909 | 0.139 | 1.000 |
| 2020-2021 | Top 12 | 0.632 | 0.167 | 0.714 |
| 2020-2021 | Top 24 | 0.737 | 0.292 | 0.714 |
| 2020-2021 | Top 36 | 0.895 | 0.375 | 0.857 |
| 2022-2023 | Top 12 | 0.375 | 0.250 | 0.750 |
| 2022-2023 | Top 24 | 0.688 | 0.396 | 0.750 |
| 2022-2023 | Top 36 | 0.750 | 0.500 | 0.750 |

The recent holdout bust-rate rise is the strongest reason not to overtrust additional broad tuning.

## Rolling Validation Results

Prior v1.1 candidate results:

- `cfbd_enriched_baseline_v1_1`: baseline reference
- `scoring_format_fit_plus_v2`: failed candidate gate
- `wr_star_capture_plus`: failed candidate gate
- `cfbd_market_share_plus`: failed candidate gate
- `draft_capital_trap_guard`: failed candidate gate
- `balanced_star_bust_frontier`: failed candidate gate
- `position_calibrated_v2`: failed candidate gate
- `ensemble_rank_blend_v1`: YELLOW stability, but not enough for v2
- v2 board: not created

New rolling audit:

- Top 12: every tested candidate was RED versus baseline.
- Top 24: every tested candidate was RED except `draft_capital_trap_guard`, which was YELLOW with no average star-capture gain.
- Top 36: `draft_capital_trap_guard` was GREEN, with average star delta +0.035 and bust delta -0.017 versus baseline.

Interpretation: the only stable positive signal is a top-36 depth-board signal, not a premium-window signal. That is useful for warning/manual-review strategy, but it does not justify broad historical retuning.

## Strict Objective Diagnostics

Diagnostic objective winners:

| Objective | Bucket | Winner | Holdout Wins | Note |
|---|---|---|---:|---|
| maximize star capture | Top 12 | baseline | 7 | baseline remains strongest premium signal |
| cap bust rate | Top 12 | baseline | 6 | baseline remains safest premium signal |
| improve WR capture | Top 12 | baseline | 7 | baseline wins WR premium objective |
| avoid draft-capital traps | Top 12 | baseline | 8 | baseline wins trap objective |
| maximize star capture | Top 24 | baseline | 4 | no challenger dominates |
| cap bust rate | Top 24 | baseline | 4 | no challenger dominates |
| improve WR capture | Top 24 | baseline | 8 | baseline dominates WR objective |
| avoid draft-capital traps | Top 24 | baseline | 9 | baseline dominates trap objective |
| maximize star capture | Top 36 | scoring-format fit | 5 | depth-board diagnostic only |
| cap bust rate | Top 36 | scoring-format fit | 4 | depth-board diagnostic only |
| improve WR capture | Top 36 | baseline | 6 | baseline remains best WR depth signal |
| avoid draft-capital traps | Top 36 | baseline | 5 | baseline remains competitive |

These diagnostics point away from broad retuning. The model's premium-window ceiling looks mostly reached with the current feature families.

## Feature Families With Remaining Tunable Signal

- Draft-capital trap guard: useful as a top-36 warning/manual-review feature; not proven as a premium rank changer.
- CFBD market share/dominator: promising but unstable; only worth a narrow WR/RB hypothesis if the hypothesis is pre-registered.
- CFBD production: useful context, but production-only ablation did not beat the balanced baseline.
- WR upside: still a real need, but broad WR-upside tuning did not produce stable premium-window gains.

## Feature Families That Appear Noisy

- Scoring-format fit: helpful for manual interpretation, but the broad candidate did not clear validation.
- Broad position calibration: did not reliably improve top-12/top-24 results.
- CFBD-only production/share blends: too noisy alone and too vulnerable to context misses.

## Biggest Non-Tunable Manual-Review Issues

Manual issue diagnostics show the remaining errors are not cleanly solved by broad feature weights:

- 15 missed stars were late-draft profiles that likely require manual scouting or role context.
- 10 high-ranked busts were late-draft profiles that also require manual scouting/role context.
- 9 high-ranked busts were general feature-family misses without a clear safe broad patch.
- 3 high-ranked busts likely required pass-catcher route/role context.
- 3 high-ranked busts had missing or unresolved source-safe CFBD features.
- 2 missed stars had missing or unresolved source-safe CFBD features.

That pattern supports manual review and source repair more than another broad tuning sweep.

## Anti-Cheat / Leakage Audit

- Names, IDs, schools, teams, and draft years were used only for identity/display/grouping/diagnostics: PASS
- Outcome labels were used only for evaluation metrics: PASS
- ADP/market data was not read or used as private score input: PASS
- No player-specific boosts, penalties, or class/team/school exceptions were added: PASS
- No new weights were tuned; only previously tested feature-family configs were evaluated: PASS
- 2024-2025 partial-window rows were excluded from tuning/evaluation: PASS

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python -m py_compile scripts\rookie_framework\audit_rookie_model_ceiling_tuning_opportunity.py tests\test_rookie_model_ceiling_tuning_opportunity.py`
- `python tests\test_rookie_model_ceiling_tuning_opportunity.py`
- `python scripts\rookie_framework\audit_rookie_model_ceiling_tuning_opportunity.py`
- `python tests\test_rookie_model_tuning_runway_v1_1.py`
- `python -m pytest tests\test_rookie_model_ceiling_tuning_opportunity.py -q`

Result: direct harnesses passed and the audit regenerated local-only exports. `pytest` was unavailable in the active Python environment (`No module named pytest`), so the direct harness result was used.

## Final Decision

Do not broad-tune next.

Recommended next action: freeze the broad historical formula for draft-use purposes, then either:

- run a narrow, pre-registered WR/role-stability or source-coverage hypothesis, or
- stop historical tuning and use manual review/draft strategy for the current board.

If Tim wants another model pass, it should be narrow-tune only. No v2 board should be created until a premium-window validation gate clears.
