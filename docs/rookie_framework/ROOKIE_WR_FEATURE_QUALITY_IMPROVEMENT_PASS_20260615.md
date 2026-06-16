# Rookie WR Feature Quality Improvement Pass

Date: 2026-06-15

Lane: Rookie framework only

## Executive Verdict

- WR feature quality: GREEN
- WR validation signal: RED
- Overall model impact: RED
- Candidate quality: not created
- Manual draft trust: YELLOW
- Tuning readiness after this pass: YELLOW
- Anti-cheat/leakage: GREEN

The pass successfully built better WR feature-quality signals from existing local CFBD cache and repaired joins, but the fixed WR-feature candidates did not earn a local experimental/manual-use board. WR validation star capture did not improve, and overall final-validation Top 24 star capture regressed.

No production ranking, private score, app wiring, Streamlit file, Outcome file, veteran file, probability, band, hidden sort key, or promoted artifact was changed.

## Files Created

- `scripts/rookie_framework/build_rookie_wr_feature_quality_pass_20260615.py`
- `tests/test_rookie_wr_feature_quality_pass_20260615.py`
- `docs/rookie_framework/ROOKIE_WR_FEATURE_QUALITY_IMPROVEMENT_PASS_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/wr_feature_quality_improvement_pass_20260615/`:

- `wr_feature_table_historical_20260615.csv`
- `wr_feature_coverage_by_year_20260615.csv`
- `wr_feature_coverage_by_round_20260615.csv`
- `wr_feature_current_coverage_20260615.csv`
- `wr_feature_quality_audit_20260615.csv`
- `wr_feature_baseline_comparison_20260615.csv`
- `wr_missed_star_diagnostics_20260615.csv`
- `wr_high_ranked_bust_diagnostics_20260615.csv`
- `wr_feature_candidate_decision_20260615.csv`
- `README_WR_FEATURE_QUALITY_IMPROVEMENT_PASS_20260615.md`

These exports are local-only and were not committed.

## Feature Families Built

Built from local CFBD player-season features and repaired joins:

- Final-season receiving profile: yards, receptions, touchdowns, volume-guarded yards per reception, yard share, reception share, touchdown share.
- Best-season receiving profile: best yards, receptions, touchdowns, yard share, reception share, touchdown share.
- Career/multi-year production profile: career yards, receptions, touchdowns, productive seasons, meaningful-share seasons.
- Breakout/production robustness proxy: multi-year production versus one-year spike.
- Production/draft-capital interaction: late-capital strong-profile flag and early-capital weak-profile warning.
- Market-share robustness: denominator-ready status and denominator-missing warning.
- WR-specific warnings: no meaningful production, one-year spike, weak early-capital profile, denominator missing, identity/join warning.

Blocked or unavailable:

- Current 2026 multi-year WR CFBD cache was not present, so historical feature logic was not applied to the current board.
- Final-year age proxy was not built because no approved source-safe age field was present in the local inputs.
- No live CFBD request was made.

## Historical WR Feature Coverage

Historical WR rows: 431

- Feature-ready rows: 386
- Missing/unresolved feature rows: 45
- Denominator-ready rows: 376
- Duplicate-selected rows: 4
- Manual-review rows: 39
- One-year spike rows: 53
- Weak early-capital warning rows: 7
- No-meaningful-production warning rows: 14

Overall feature coverage verdict: GREEN

Coverage by draft round:

| Round | WR Rows | Feature Ready | Ready Rate | Denominator Ready | Denominator Rate |
|---:|---:|---:|---:|---:|---:|
| 1 | 54 | 51 | 0.944 | 51 | 0.944 |
| 2 | 65 | 59 | 0.908 | 59 | 0.908 |
| 3 | 63 | 57 | 0.905 | 55 | 0.873 |
| 4 | 62 | 55 | 0.887 | 55 | 0.887 |
| 5 | 52 | 46 | 0.885 | 43 | 0.827 |
| 6 | 71 | 67 | 0.944 | 64 | 0.901 |
| 7 | 64 | 51 | 0.797 | 49 | 0.766 |

Lowest year coverage rates:

| Year | WR Rows | Feature Ready | Ready Rate | Denominator Ready | Denominator Rate |
|---:|---:|---:|---:|---:|---:|
| 2011 | 26 | 20 | 0.769 | 20 | 0.769 |
| 2013 | 26 | 21 | 0.808 | 21 | 0.808 |
| 2010 | 28 | 23 | 0.821 | 23 | 0.821 |
| 2016 | 31 | 26 | 0.839 | 26 | 0.839 |
| 2014 | 33 | 28 | 0.848 | 26 | 0.788 |

## Current 2026 Coverage

Current board WR rows: 90

- Current feature-ready rows: 0
- Current denominator-ready rows: 0

Reason: no current 2026 multi-year CFBD WR feature cache was present in the approved local inputs. The pass did not fetch live data and did not apply historical feature logic to the current board.

## Baseline vs WR-Feature Candidates

Validation split: 2022-2023

Overall year-class metrics:

| Model | Bucket | Stars Captured | Star Capture | Bust Rate |
|---|---:|---:|---:|---:|
| `cfbd_enriched_baseline_v1_1` | Top 12 | 6 / 16 | 0.375 | 0.250 |
| `cfbd_enriched_baseline_v1_1` | Top 24 | 11 / 16 | 0.688 | 0.396 |
| `cfbd_enriched_baseline_v1_1` | Top 36 | 12 / 16 | 0.750 | 0.500 |
| `wr_feature_enhanced_conservative` | Top 12 | 5 / 16 | 0.312 | 0.333 |
| `wr_feature_enhanced_conservative` | Top 24 | 10 / 16 | 0.625 | 0.375 |
| `wr_feature_enhanced_conservative` | Top 36 | 11 / 16 | 0.688 | 0.528 |
| `wr_feature_enhanced_assertive` | Top 12 | 5 / 16 | 0.312 | 0.333 |
| `wr_feature_enhanced_assertive` | Top 24 | 10 / 16 | 0.625 | 0.354 |
| `wr_feature_enhanced_assertive` | Top 36 | 11 / 16 | 0.688 | 0.514 |

WR-only validation metrics:

| Model | Bucket | WR Stars Captured | WR Star Capture | WR Bust Rate |
|---|---:|---:|---:|---:|
| `cfbd_enriched_baseline_v1_1` | Top 12 | 3 / 4 | 0.750 | 0.250 |
| `cfbd_enriched_baseline_v1_1` | Top 24 | 3 / 4 | 0.750 | 0.375 |
| `cfbd_enriched_baseline_v1_1` | Top 36 | 3 / 4 | 0.750 | 0.472 |
| `wr_feature_enhanced_conservative` | Top 12 | 3 / 4 | 0.750 | 0.250 |
| `wr_feature_enhanced_conservative` | Top 24 | 3 / 4 | 0.750 | 0.375 |
| `wr_feature_enhanced_conservative` | Top 36 | 3 / 4 | 0.750 | 0.472 |
| `wr_feature_enhanced_assertive` | Top 12 | 3 / 4 | 0.750 | 0.250 |
| `wr_feature_enhanced_assertive` | Top 24 | 3 / 4 | 0.750 | 0.417 |
| `wr_feature_enhanced_assertive` | Top 36 | 3 / 4 | 0.750 | 0.472 |

## Candidate Decision

No experimental/manual-use WR-feature candidate output was created.

Candidate gate results:

- `wr_feature_enhanced_conservative`: not created. WR validation star capture did not improve, and overall Top 24 star capture regressed by 0.063.
- `wr_feature_enhanced_assertive`: not created. WR validation star capture did not improve, WR Top 24 bust rate worsened by 0.042, and overall Top 24 star capture regressed by 0.063.

The new features are useful for diagnostics and future feature work, but they did not yet create a better ranking candidate.

## Anti-Cheat / Leakage Audit

- PASS: no player-name, alias, player-ID, school, team, draft-year, or known-outcome tuning rule was added.
- PASS: names appear only in diagnostics.
- PASS: outcome labels are evaluation-only.
- PASS: ADP, market, projections, public rankings, consensus, trade calculators, and draft-kit ranks were not used as private score inputs.
- PASS: missing denominator rows were flagged and not zero-filled as positive evidence.
- PASS: 2024-2025 partial-window rows were not used.
- PASS: no live API key or secret was printed, logged, exported, or committed.
- PASS: no production/app/promoted artifact was created.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `python -m py_compile scripts\rookie_framework\build_rookie_wr_feature_quality_pass_20260615.py tests\test_rookie_wr_feature_quality_pass_20260615.py`
- `python tests\test_rookie_wr_feature_quality_pass_20260615.py`
- `python scripts\rookie_framework\build_rookie_wr_feature_quality_pass_20260615.py`
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
- `python tests\test_rookie_model_tuning_runway_v1_1.py`
- `python tests\test_rookie_cfbd_enriched_baseline_runway_v1.py`
- `python tests\test_rookie_cfbd_identity_join_repair_v1.py`
- `python tests\test_rookie_cfbd_historical_feature_cache_v1.py`
- `python tests\test_rookie_historical_allowlist_qa_expanded_baseline_v1.py`
- `python tests\test_rookie_experimental_tuning_candidate_v1.py`
- `python tests\test_rookie_backtest_framework_v01.py`
- `python -m pytest tests\test_rookie_wr_feature_quality_pass_20260615.py -q`
- `Select-String -Path scripts\rookie_framework\build_rookie_wr_feature_quality_pass_20260615.py -Pattern 'api_key|CFBD_API|if\s+.*player|player_name\s*==|private_score|probability|band|streamlit|outcome_probability|hidden sort' -CaseSensitive:$false`

Pytest was unavailable: `No module named pytest`. Direct harnesses passed.

## Recommended Next Rookie-Only Task

Do not create a v2 board yet. The next best task is a current-2026 WR feature ingestion path: build the same WR feature families for the current rookie pool from source-safe local CFBD/current evidence, then rerun a narrow candidate audit only after current coverage exists.
