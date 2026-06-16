# Rookie Final Manual Draft Kit Local Data Fill

Date: 2026-06-16

Verdict: YELLOW_GREEN for data-fill coverage, GREEN for draft-use readability, GREEN for data integrity, GREEN for anti-cheat/leakage.

This patch fills display-only draft-room fields in the already-cleaned frozen rookie draft kit. It does not tune, rescore, reorder, change draft actions, or change the model formula.

## Scope

Tracked files added:

- `scripts/rookie_framework/build_rookie_final_manual_draft_kit_local_data_fill_20260616.py`
- `tests/test_rookie_final_manual_draft_kit_local_data_fill_20260616.py`
- `docs/rookie_framework/ROOKIE_FINAL_MANUAL_DRAFT_KIT_LOCAL_DATA_FILL_20260616.md`

Local-only output directory:

- `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_data_fill_20260616/`

Preview:

- `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_data_fill_20260616/preview/index.html`

Final draft-use CSV:

- `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_data_fill_20260616/rookie_2026_final_manual_draft_board_display_cleanup_data_filled_20260616.csv`

## Guardrails

- Formula changed: no
- Formula remains: `cfbd_enriched_baseline_v1_1`
- Board order changed: no
- Tuning performed: no
- Rescoring performed: no
- Reordering performed: no
- Draft actions changed: no
- Production ranking created: no
- Streamlit/app production wiring changed: no
- Outcome/veteran files touched: no
- ADP/market used as private score input: no
- ADP/market use: display-only

## Local Sources Used

| Field | Source | Path | Use |
|---|---|---|---|
| `ADP / Market` | Rookie ADP, fallback FantasyPros overall ADP | `local_exports/model_v4/prospect_sources/latest/files/source_project/data/market/processed/rookie_adp_2026_04_23_to_2026_05_17.csv`; `local_exports/model_v4/prospect_sources/latest/files/source_project/data/fantasypros/processed/fantasypros_overall_adp_2026.csv` | display-only |
| `NFL Team` | Admitted current prospect identity spine | `local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/admitted_current_prospect_identity_spine.csv` | display-only |
| `Age` | Drop Decision prospect age export | `C:/Users/smcol/Documents/Vacation/Niners-War-Room-drop-decision/local_exports/model_v4/prospect_age/latest/player_age_2026.csv` | display-only, local review only |
| `Depth Chart / Role` | Existing role-tag fallback from display-cleanup export | `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616/` | display-only |
| `NFL Draft Capital` | Existing cleanup/current board draft-capital display | `local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616/` | display-only |

No new data was pulled from the network. No source data was edited.

## Coverage

| Field | Populated Rows | `needs_data` Rows |
|---|---:|---:|
| `ADP / Market` | 46 | 8 |
| `NFL Team` | 46 | 8 |
| `Age` | 27 | 27 |
| `Depth Chart / Role` | 11 | 43 |
| `NFL Draft Capital` | 54 | 0 |

Remaining gaps:

- `ADP / Market`: 8 rows still need display-only ADP/market data.
- `NFL Team`: 8 rows still need a source-safe team assignment.
- `Age`: 27 rows still need age or DOB.
- `Depth Chart / Role`: 43 rows still need true NFL depth-chart/role data; current values remain role-tag fallback or `needs_data`.
- `NFL Draft Capital`: no current display gap.

## Output Shape

The cleaned display layout is preserved:

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

Redundant rank columns remain removed. The visible `tier` column remains removed. Tier banners remain in the HTML preview.

## Local Exports

Created local-only exports:

- `rookie_2026_final_manual_draft_board_display_cleanup_data_filled_20260616.csv`
- `rookie_2026_draft_day_quick_sheet_display_cleanup_data_filled_20260616.csv`
- `rookie_2026_warning_priority_display_cleanup_data_filled_20260616.csv`
- `rookie_2026_display_data_fill_coverage_20260616.csv`
- `rookie_2026_display_data_fill_sources_20260616.csv`
- `rookie_2026_display_data_fill_guardrails_20260616.csv`
- `rookie_2026_display_data_fill_verdicts_20260616.csv`
- `README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_LOCAL_DATA_FILL_20260616.md`
- `preview/index.html`

These exports are local-only and are not committed.

## Validation

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python tests\test_rookie_final_manual_draft_kit_local_data_fill_20260616.py`
- `python scripts\rookie_framework\build_rookie_final_manual_draft_kit_local_data_fill_20260616.py`
- `python -m py_compile scripts\rookie_framework\build_rookie_final_manual_draft_kit_local_data_fill_20260616.py tests\test_rookie_final_manual_draft_kit_local_data_fill_20260616.py`

Direct harness result: passed.

The harness verifies:

- Board order did not change.
- Formula guardrail remains unchanged.
- ADP/market remains display-only.
- Missing values are not invented.
- Tier banners remain present in HTML.
- Duplicate rank columns remain removed.
- Coverage counts are reported.

## Anti-Cheat / Leakage

PASS:

- No tuning.
- No rescoring.
- No board reordering.
- No draft-action change.
- No ADP/market private-score input.
- No invented missing values.
- No production rankings.
- No app/Streamlit production wiring.
- No outcome columns.
- No veteran files.
- No probabilities.
- No app-readable probability bands.
- No hidden sort keys.
- No promoted artifacts.
- `data/` and `local_exports/` remain uncommitted.
