# Rookie Current 2026 CFBD Feature Ingestion

Date: 2026-06-15

Lane: Rookie framework only

## Executive Verdict

- Current feature ingestion: GREEN
- WR coverage: GREEN
- Ranking usefulness: YELLOW
- Manual draft trust: YELLOW
- Anti-cheat/leakage: GREEN

The current 2026 CFBD ingestion path now exists. It joins the current rookie advisory board to source-safe CFBD regular-season production, team denominator, market-share/dominator, and WR feature-quality context.

No tuning was performed. No v2 board was created. The local feature-ingested manual board preserves the existing rookie rank order and appends CFBD context/warnings only.

## Why Prior 2026 WR Coverage Was 0

The WR feature-quality pass had historical CFBD player-season features and repaired historical joins, but it did not have a current 2026 feature cache or current-rookie identity join. Because no current 2024/2025 CFBD player/team feature table existed, the historical WR logic could not be applied to the 2026 board.

This pass created the current cache and current identity join.

## Files Created

- `scripts/rookie_framework/build_current_2026_cfbd_feature_ingestion.py`
- `tests/test_current_2026_cfbd_feature_ingestion.py`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_CFBD_FEATURE_INGESTION_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/`:

- `cfbd_current_2026_fetch_manifest_20260615.csv`
- `cfbd_current_2026_player_features_20260615.csv`
- `current_2026_cfbd_feature_join_20260615.csv`
- `current_2026_cfbd_feature_coverage_by_position_20260615.csv`
- `current_2026_wr_feature_quality_table_20260615.csv`
- `current_2026_feature_ingested_manual_board_20260615.csv`
- `current_2026_rank_movement_20260615.csv`
- `README_CURRENT_2026_CFBD_FEATURE_INGESTION_20260615.md`

These exports are local-only and were not committed.

## CFBD Cache

Approved endpoint categories used:

- `/stats/player/season`, regular season, passing
- `/stats/player/season`, regular season, rushing
- `/stats/player/season`, regular season, receiving
- `/stats/season`, regular season, team denominators

Seasons cached:

- 2024
- 2025

The first run populated the local cache. The final validation run used cache hits:

| Season | Endpoint | Category | Status | Rows |
|---:|---|---|---|---:|
| 2024 | `/stats/player/season` | passing | cache_hit | 7014 |
| 2024 | `/stats/player/season` | rushing | cache_hit | 15700 |
| 2024 | `/stats/player/season` | receiving | cache_hit | 20180 |
| 2024 | `/stats/season` | team_denominators | cache_hit | 8442 |
| 2025 | `/stats/player/season` | passing | cache_hit | 7364 |
| 2025 | `/stats/player/season` | rushing | cache_hit | 16465 |
| 2025 | `/stats/player/season` | receiving | cache_hit | 21095 |
| 2025 | `/stats/season` | team_denominators | cache_hit | 8568 |

No API key or secret was printed, exported, or committed.

## Current Feature Coverage

Current board rows: 185

| Position | Rows | Matched | Unmatched | Denominator Ready | Match Rate | Denominator Rate |
|---|---:|---:|---:|---:|---:|---:|
| QB | 8 | 8 | 0 | 7 | 1.000 | 0.875 |
| RB | 46 | 42 | 4 | 38 | 0.913 | 0.826 |
| WR | 90 | 87 | 3 | 83 | 0.967 | 0.922 |
| TE | 41 | 40 | 1 | 40 | 0.976 | 0.976 |

WR coverage is now usable for manual review: 87 of 90 current WR rows matched, and 83 have denominator-ready market-share context.

## Remaining Unmatched Current Rows

| Rank | Player | Position | School | Status |
|---:|---|---|---|---|
| 54 | Chip Trayanum | RB | Toledo | unmatched_current_identity |
| 57 | Mike Washington | RB | Arkansas | unmatched_current_identity |
| 73 | Reggie Virgil | WR | Texas Tech | unmatched_current_identity |
| 81 | Jam Miller | RB | Alabama | unmatched_current_identity |
| 112 | Jaydn Ott | RB | Oklahoma | unmatched_current_identity |
| 136 | DJ Rogers | TE | TCU | unmatched_current_identity |
| 146 | Ja'Mori Maclin | WR | Kentucky | unmatched_current_identity |
| 163 | Ryan Niblett | WR | Texas | unmatched_current_identity |

These remain warning-visible and are not silently filled.

## Warning Visibility

The feature-ingested board preserves the original `warning_flags` column and adds `cfbd_warning_flags`.

Current CFBD warning examples include:

- `CFBD_UNMATCHED_CURRENT_IDENTITY`
- `CFBD_DENOMINATOR_MISSING`
- `CFBD_NO_2025_PROFILE_SELECTED`

The warnings remain manual-review context. They are not hidden sort keys and are not production gates.

## WR Feature Quality Context

The local WR feature table now includes current versions of the historical WR feature families:

- current/final receiving profile
- best-season receiving profile
- career/multi-year receiving profile
- market-share/dominator context
- denominator status
- one-year spike warnings
- weak/no production warnings
- WR feature signal score
- WR warning penalty

Top current WR feature signal rows are diagnostic only; they do not change rank order.

## Feature-Ingested Manual Board

Created:

- `current_2026_feature_ingested_manual_board_20260615.csv`

This is a local/manual-use export only. It is not a production ranking, not app-readable, and not a v2 board.

Fields appended include CFBD production, team denominator, market-share/dominator, source-safety, promotion guardrails, and warning flags.

## Rank Movement

Biggest current-board rank movers: none.

All rank deltas are 0 because this pass did not tune, rescore, or reorder the board. Rank was intentionally preserved while feature context was appended for manual review.

Examples:

| Player | Position | Old Rank | Feature-Ingested Rank | Delta |
|---|---|---:|---:|---:|
| Jeremiyah Love | RB | 1 | 1 | 0 |
| KC Concepcion | WR | 2 | 2 | 0 |
| Makai Lemon | WR | 3 | 3 | 0 |
| Denzel Boston | WR | 4 | 4 | 0 |
| Germie Bernard | WR | 5 | 5 | 0 |

## Candidate / V2 Decision

Local/manual-use feature-ingested board created: yes

Experimental v2 candidate board created: no

Reason: this was an ingestion pass, not tuning. Coverage is now strong enough to support a future narrow candidate audit, but no ranking formula or score changed in this pass.

## Anti-Cheat / Leakage Audit

- PASS: no Outcome files were touched.
- PASS: no production rankings, private scores, outcome columns, app wiring, Streamlit files, veteran files, probabilities, bands, hidden sort keys, or promoted artifacts were touched.
- PASS: no player-specific tuning rules were added.
- PASS: no ADP, market, public rankings, projections, consensus, trade values, or draft-kit ranks were used as private score inputs.
- PASS: CFBD fields are factual regular-season production and team denominator context.
- PASS: missing rows and denominator gaps remain warning-visible.
- PASS: no secret or API key was printed, logged, exported, or committed.
- PASS: `data/` and `local_exports/` were not committed.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `python -m py_compile scripts\rookie_framework\build_current_2026_cfbd_feature_ingestion.py tests\test_current_2026_cfbd_feature_ingestion.py`
- `python tests\test_current_2026_cfbd_feature_ingestion.py`
- `python scripts\rookie_framework\build_current_2026_cfbd_feature_ingestion.py`
- `python scripts\rookie_framework\build_rookie_review_board_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_shadow_ranking_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_production_candidate_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_analyzer_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_day_simulation_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_ranking_v01.py`
- `python scripts\rookie_framework\build_rookie_historical_outcome_labels_v1.py`
- `python scripts\rookie_framework\backtest_rookie_ranking_model_v01.py`
- `python tests\test_rookie_wr_feature_quality_pass_20260615.py`
- `python -m pytest tests\test_current_2026_cfbd_feature_ingestion.py -q`
- `Select-String -Path scripts\rookie_framework\build_current_2026_cfbd_feature_ingestion.py -Pattern 'api_key|CFBD_API|if\s+.*player|player_name\s*==|private_score|probability|band|streamlit|outcome_probability|hidden sort' -CaseSensitive:$false`

Pytest was unavailable: `No module named pytest`. Direct harnesses passed. Safety-scan hits were limited to configuration variable names, generic guard clauses, and guardrail text; no secret values or player-specific tuning rules were found.

## Recommended Next Rookie-Only Task

Run a narrow current-feature candidate audit that compares the existing current board against a local/manual-only CFBD-context candidate. Do not promote or app-wire it unless a later prompt explicitly approves production integration.
