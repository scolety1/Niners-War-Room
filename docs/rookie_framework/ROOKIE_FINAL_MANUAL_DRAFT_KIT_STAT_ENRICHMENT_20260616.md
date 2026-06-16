# Rookie Final Manual Draft Kit Stat Enrichment

Date: 2026-06-16

Verdict: GREEN for display enrichment, YELLOW for data coverage, GREEN for manual-question quality, GREEN for manual draft-use readiness, GREEN for anti-cheat/leakage.

This patch improves the local/manual-use frozen rookie draft kit and HTML preview without changing the model formula, board order, production rankings, app wiring, private scores, probabilities, or promoted artifacts.

## Scope

Tracked files added:

- `scripts/rookie_framework/build_rookie_final_manual_draft_kit_stat_enrichment_20260616.py`
- `tests/test_rookie_final_manual_draft_kit_stat_enrichment_20260616.py`
- `docs/rookie_framework/ROOKIE_FINAL_MANUAL_DRAFT_KIT_STAT_ENRICHMENT_20260616.md`

Local-only output directory:

- `local_exports/rookie_framework/final_manual_draft_kit_stat_enrichment_20260616/`

Preview:

- `local_exports/rookie_framework/final_manual_draft_kit_stat_enrichment_20260616/preview/index.html`

## Formula And Order Guardrails

- Main formula changed: no
- Formula remains: `cfbd_enriched_baseline_v1_1`
- Board order changed: no
- Rescoring performed: no
- Reordering performed: no
- Production ranking created: no
- Streamlit/app production wiring changed: no
- Outcome/veteran files touched: no
- ADP/market used as private score input: no

## Display Column Upgrade

The enriched board, quick sheet, warning sheet, manual checklist, tier cards, and HTML preview now prioritize these draft-room columns:

1. `overall_rank`
2. `player`
3. `position`
4. `nfl_team`
5. `depth_chart_position_or_role`
6. `age`
7. `nfl_draft_capital`
8. `rookie_adp_or_market_rank`
9. `nwr_overall_ranking`
10. `model_rank`
11. `upside_score_or_band`
12. `bust_risk_percent_or_band`
13. `tier`
14. `draft_action`
15. `warning_severity`
16. `main_positive_reason`
17. `main_risk`
18. `manual_question`

`rookie_adp_or_market_rank` is display-only and remains excluded from private/model score logic.

`upside_score_or_band` and `bust_risk_percent_or_band` are derived only from existing local model/export fields. They are not exact probabilities, not production probability bands, and not app-readable outcome artifacts.

## Field Coverage

| Field | Populated Rows | Missing / needs_data Rows | Handling |
|---|---:|---:|---|
| `nfl_team` | 46 | 8 | Source-safe local value if present; otherwise `needs_data` |
| `depth_chart_position_or_role` | 11 | 43 | Local role/archetype context if present; otherwise `needs_data` |
| `age` | 0 | 54 | Source-safe local value if present; otherwise `needs_data` |
| `nfl_draft_capital` | 54 | 0 | Display from existing draft-capital fields |
| `rookie_adp_or_market_rank` | 0 | 54 | Display-only; not used in model/private score |
| `upside_score_or_band` | 54 | 0 | Existing score plus label, not probability |
| `bust_risk_percent_or_band` | 54 | 0 | Existing score plus label, not probability |

Data coverage verdict: YELLOW because ADP/market rank, age/DOB, and most NFL depth-chart/role fields still need Tim-provided or otherwise approved local source files.

## Manual Question Improvement

The previous kit had repetitive tier-level manual questions. The enriched kit now creates player-specific questions from available flags/features:

- Unmatched/neutral-feature rows ask whether the player is missing model context because of a join/data issue.
- Critical trap-guard rows ask whether draft capital and role actually support the rank.
- True injury/manual flags ask whether the injury concern is still active enough to change the same-tier decision.
- Large feature-driven rank movers ask whether the move is supported by NFL team, role, and draft capital.
- WRs ask about target-earning path and route/separation evidence when those flags exist.
- RBs ask about early-down, goal-line, and first-down role path.
- TEs/QBs ask whether the player is an actual exception case in a 10-team 1QB non-PPR format.

Missing `injury_history_score` by itself is treated as a data gap, not as an active injury concern.

## Missing Data Request For Tim

To improve the draft-room sheet further, provide the following files/columns:

1. Display-only ADP/market rank file
   - Columns: `player_name`, `position`, `adp_or_market_rank`, `source_name`, `as_of_date`
   - Handling: display-only; excluded from private/model score.

2. NFL team assignment file
   - Columns: `player_name`, `position`, `nfl_team`, `source_name`, `as_of_date`
   - Handling: existing local board has NFL team for many rows; Tim should verify final assignments.

3. NFL depth-chart / role file
   - Columns: `player_name`, `position`, `nfl_team`, `depth_chart_position`, `projected_role`, `role_confidence`, `source_name`, `as_of_date`
   - Handling: display/manual-review context only unless separately approved.

4. Age / DOB file
   - Columns: `player_name`, `position`, `date_of_birth` or `age_on_draft_day`, `source_name`
   - Handling: blank/`needs_data` until available.

5. Final NFL draft-capital file
   - Columns: `player_name`, `position`, `nfl_team`, `draft_round`, `overall_pick`, `source_name`
   - Handling: existing local draft-capital values are displayed where present; Tim should verify final source.

## Local Exports

Created local-only exports:

- `rookie_2026_final_manual_draft_board_stat_enriched_20260616.csv`
- `rookie_2026_draft_day_quick_sheet_stat_enriched_20260616.csv`
- `rookie_2026_warning_priority_stat_enriched_20260616.csv`
- `rookie_2026_manual_decisions_checklist_stat_enriched_20260616.csv`
- `rookie_2026_tier_cards_stat_enriched_20260616.csv`
- `rookie_2026_field_coverage_stat_enrichment_20260616.csv`
- `rookie_2026_missing_data_request_for_tim_20260616.csv`
- `rookie_2026_stat_enrichment_verdicts_20260616.csv`
- `README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_STAT_ENRICHMENT_20260616.md`
- `preview/index.html`

These exports are local-only and are not committed.

## Validation

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python -m py_compile scripts\rookie_framework\build_rookie_final_manual_draft_kit_stat_enrichment_20260616.py tests\test_rookie_final_manual_draft_kit_stat_enrichment_20260616.py`
- `python tests\test_rookie_final_manual_draft_kit_stat_enrichment_20260616.py`
- `python scripts\rookie_framework\build_rookie_final_manual_draft_kit_stat_enrichment_20260616.py`

Validation result: GREEN.

## Anti-Cheat / Leakage

PASS:

- No tuning.
- No rescoring.
- No board reordering.
- No ADP/market private-score input.
- No invented ADP, team, role, age, draft capital, upside, or bust values.
- Missing values remain `needs_data`.
- No production rankings.
- No app/Streamlit production wiring.
- No outcome columns.
- No veteran files.
- No probabilities.
- No app-readable probability bands.
- No promoted artifacts.
- `data/` and `local_exports/` remain uncommitted.
