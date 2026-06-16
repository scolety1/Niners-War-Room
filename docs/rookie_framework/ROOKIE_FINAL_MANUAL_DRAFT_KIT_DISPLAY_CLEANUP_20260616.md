# Rookie Final Manual Draft Kit Display Cleanup

Date: 2026-06-16

Verdict: GREEN for display cleanup quality, GREEN for draft-use readability, GREEN for data integrity, GREEN for anti-cheat/leakage.

This patch creates a cleaner local/manual-use preview for the frozen rookie draft kit. It does not tune, rescore, reorder, ingest new data, or promote anything to production.

## Scope

Tracked files added:

- `scripts/rookie_framework/build_rookie_final_manual_draft_kit_display_cleanup_20260616.py`
- `tests/test_rookie_final_manual_draft_kit_display_cleanup_20260616.py`
- `docs/rookie_framework/ROOKIE_FINAL_MANUAL_DRAFT_KIT_DISPLAY_CLEANUP_20260616.md`

Local-only output directory:

- `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616/`

Preview:

- `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616/preview/index.html`

## Guardrails

- Formula changed: no
- Formula remains: `cfbd_enriched_baseline_v1_1`
- Board order changed: no
- Tuning performed: no
- Rescoring performed: no
- Reordering performed: no
- New ADP/team/depth-chart/age data ingested: no
- Production ranking created: no
- Streamlit/app production wiring changed: no
- Outcome/veteran files touched: no
- ADP/market used as private score input: no

## Display Cleanup

The prior stat-enriched preview displayed all enriched row fields, including repeated rank fields and the tier field. The cleanup preview now:

- Groups the main board by tier banner.
- Removes the visible `tier` column from the main table.
- Displays only one rank column.
- Keeps missing values as `needs_data`.
- Keeps the frozen order inside each tier and across the full board.

Tier banners:

- Tier 1 - Priority Targets
- Tier 2 - Strong Considers
- Tier 3 - Value / Fit Targets
- Tier 4 - Manual Review Upside
- Tier 5 - Avoid / Hold Unless Price Drops, if a future frozen board contains Tier 5 rows

Current frozen board tier counts:

| Tier | Rows |
|---|---:|
| Tier 1 - Priority Targets | 9 |
| Tier 2 - Strong Considers | 15 |
| Tier 3 - Value / Fit Targets | 12 |
| Tier 4 - Manual Review Upside | 18 |
| Tier 5 - Avoid / Hold Unless Price Drops | 0 |

## Displayed Columns

Before cleanup, the enriched preview included:

- `overall_rank`
- `player`
- `position`
- `nfl_team`
- `depth_chart_position_or_role`
- `age`
- `nfl_draft_capital`
- `rookie_adp_or_market_rank`
- `nwr_overall_ranking`
- `model_rank`
- `upside_score_or_band`
- `bust_risk_percent_or_band`
- `tier`
- `draft_action`
- `warning_severity`
- `main_positive_reason`
- `main_risk`
- `manual_question`
- additional guardrail/context columns

After cleanup, the main display/export columns are:

1. `Rank`
2. `Player`
3. `Pos`
4. `NFL Team`
5. `Depth Chart / Role`
6. `Age`
7. `NFL Draft Capital`
8. `ADP / Market`
9. `Upside`
10. `Bust Risk`
11. `Draft Action`
12. `Warning Severity`
13. `Main Positive Reason`
14. `Main Risk`
15. `Manual Question`

`Rank` is backed by the frozen overall/model rank. `overall_rank`, `nwr_overall_ranking`, and `model_rank` are intentionally not repeated in the displayed preview/export.

## Local Exports

Created local-only exports:

- `rookie_2026_final_manual_draft_board_display_cleanup_20260616.csv`
- `rookie_2026_draft_day_quick_sheet_display_cleanup_20260616.csv`
- `rookie_2026_warning_priority_display_cleanup_20260616.csv`
- `rookie_2026_tier_summary_display_cleanup_20260616.csv`
- `rookie_2026_display_cleanup_guardrails_20260616.csv`
- `rookie_2026_display_cleanup_verdicts_20260616.csv`
- `README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_DISPLAY_CLEANUP_20260616.md`
- `preview/index.html`

These exports are local-only and are not committed.

## Validation

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python tests\test_rookie_final_manual_draft_kit_display_cleanup_20260616.py`
- `python scripts\rookie_framework\build_rookie_final_manual_draft_kit_display_cleanup_20260616.py`
- `python -m py_compile scripts\rookie_framework\build_rookie_final_manual_draft_kit_display_cleanup_20260616.py tests\test_rookie_final_manual_draft_kit_display_cleanup_20260616.py`

Direct harness result: passed.

The harness verifies:

- Board order did not change.
- Formula guardrail remains unchanged.
- Tier banners are present in HTML.
- Redundant rank columns are removed from the display export.
- Visible `tier` column is removed from the main preview/export.
- No new data is invented; missing values stay `needs_data`.

## Anti-Cheat / Leakage

PASS:

- No tuning.
- No rescoring.
- No board reordering.
- No new ADP/team/depth-chart/age ingestion.
- No ADP/market private-score input.
- No production rankings.
- No app/Streamlit production wiring.
- No outcome columns.
- No veteran files.
- No probabilities.
- No app-readable probability bands.
- No hidden sort keys.
- No promoted artifacts.
- `data/` and `local_exports/` remain uncommitted.
