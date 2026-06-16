# Rookie Draft-Capital Trap Guard Overlay

Date: 2026-06-16

Lane: Rookie framework only

## Executive Verdict

- Overlay quality: GREEN
- Draft-use readiness: YELLOW
- Manual draft trust: YELLOW
- Anti-cheat/leakage: GREEN
- Main ranking formula changed: no

This pass adds a narrow draft-capital-trap warning/manual-review overlay to the current 2026 feature-aware draft-use board. It does not tune weights, create a v2 formula, reorder the board, or replace `cfbd_enriched_baseline_v1_1`.

The overlay is intentionally conservative: it flags late, very late, or missing draft-capital context inside the top 54, especially when paired with low evidence, high bust risk, source-limited notes, weak CFBD production/share, or missing CFBD profile context. The result is a clearer manual draft board, not a production ranking.

No production ranking, private score change, app wiring, Streamlit file, Outcome file, veteran file, probability, band, hidden sort key, or promoted artifact was created.

## Inputs Reviewed

- `docs/rookie_framework/ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md`
- `local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/current_2026_feature_aware_candidate_board_20260615.csv`
- `local_exports/rookie_framework/current_2026_top36_draft_decision_review_20260615/draft_day_decision_sheet_20260615.csv`

## Files Created

- `scripts/rookie_framework/build_draft_capital_trap_guard_overlay.py`
- `tests/test_draft_capital_trap_guard_overlay.py`
- `docs/rookie_framework/ROOKIE_DRAFT_CAPITAL_TRAP_GUARD_OVERLAY_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/draft_capital_trap_guard_overlay_20260615/`:

- `draft_capital_trap_guard_top54_overlay_20260615.csv`
- `draft_capital_trap_guard_flagged_players_20260615.csv`
- `draft_capital_trap_guard_final_draft_board_20260615.csv`
- `draft_capital_trap_guard_verdicts_20260615.csv`
- `README_DRAFT_CAPITAL_TRAP_GUARD_OVERLAY_20260615.md`

Final local/manual-use draft board:

- `local_exports/rookie_framework/draft_capital_trap_guard_overlay_20260615/draft_capital_trap_guard_final_draft_board_20260615.csv`

These exports are local-only and must not be committed.

## Overlay Definition

Trap-guard flags are warning/manual-review only. They do not change rank order.

The overlay flags a top-54 player when existing board fields show one or more of:

- round 3 player inside the top 24 who needs manual confirmation
- round 3 player with fragility flags
- round 4-plus draft capital inside the top 54
- very late round 6-plus profile inside the top 54
- unknown or missing draft-capital context inside the top 54
- low evidence confidence
- high bust-risk index
- source-limited warning
- missing CFBD denominator/profile context
- unmatched current CFBD features
- no standout CFBD production/share edge

Severity:

- `manual_review`: draft-capital trap check is required, but source support is not an automatic hold.
- `hard_manual_review`: do not draft from rank alone; Tim must actively clear the trap-guard question.
- `none`: no draft-capital-trap overlay; existing manual/injury/source warnings may still apply.

## Flagged Top-54 Players

Summary:

- Total top-54 rows: 54
- Trap-guard flagged rows: 45
- `manual_review`: 3
- `hard_manual_review`: 42

### Manual Review

| Rank | Player | Pos | Reason |
|---:|---|---|---|
| 8 | Chris Bell | WR | Round 3 player in top 24; source-limited warning visible. |
| 9 | Zachariah Branch | WR | Round 3 player in top 24; source-limited warning visible. |
| 12 | Skyler Bell | WR | Round 4 draft capital; source-limited warning visible. |

### Hard Manual Review

| Rank | Player | Pos | Reason |
|---:|---|---|---|
| 10 | Antonio Williams | WR | Round 3 top-24 profile with low evidence, high bust risk, source-limited warning, and no standout CFBD edge. |
| 11 | Jonah Coleman | RB | Round 4 profile with low evidence, high bust risk, and source-limited warning. |
| 13 | Brenen Thompson | WR | Round 4 profile with low evidence and source-limited warning. |
| 14 | Elijah Sarratt | WR | Round 4 profile with low evidence and source-limited warning. |
| 15 | Emmett Johnson | RB | Round 6 profile with source-limited warning and very late overall pick. |
| 16 | Kaytron Allen | RB | Round 6 profile with source-limited warning and very late overall pick. |
| 17 | Adam Randall | RB | Round 6 profile with source-limited warning and very late overall pick. |
| 18 | Josh Cameron | WR | Round 6 profile with low evidence, source-limited warning, and very late overall pick. |
| 19 | Nicholas Singleton | RB | Round 6 profile with source-limited warning and very late overall pick. |
| 20 | Barion Brown | WR | Round 6 profile with low evidence, high bust risk, source-limited warning, no standout CFBD edge, and very late overall pick. |
| 21 | Demond Claiborne | RB | Round 7 profile with source-limited warning and very late overall pick. |
| 22 | Lewis Bond | WR | Round 7 profile with low evidence and very late overall pick. |
| 23 | J'Mari Taylor | RB | Missing draft-capital context inside top 54 with source-limited warning. |
| 24 | Kentrel Bullock | RB | Missing draft-capital context with low evidence, high bust risk, and source-limited warning. |
| 25 | Eric McAlister | WR | Missing draft-capital context with low evidence and source-limited warning. |
| 26 | Kejon Owens | RB | Missing draft-capital context with low evidence and high bust risk. |
| 27 | Sieh Bangura | RB | Missing draft-capital context with low evidence and high bust risk. |
| 28 | Chris Brazzell | WR | Missing draft-capital context with low evidence and source-limited warning. |
| 29 | Robert Henry Jr. | RB | Missing draft-capital context with low evidence, high bust risk, and source-limited warning. |
| 30 | Seth McGowan | RB | Round 8 profile with source-limited warning and very late overall pick. |
| 31 | Jacob De Jesus | WR | Missing draft-capital context with low evidence and high bust risk. |
| 32 | Omar Cooper | WR | Missing draft-capital context with source-limited warning. |
| 33 | Dominic Richardson | RB | Missing draft-capital context with low evidence and high bust risk. |
| 34 | Devin Voisin | WR | Missing draft-capital context with low evidence and high bust risk. |
| 35 | Hank Beatty | WR | Missing draft-capital context with low evidence. |
| 36 | O'Mega Blake | WR | Missing draft-capital context with low evidence. |
| 37 | Emmanuel Henderson | WR | Missing draft-capital context with low evidence and source-limited warning. |
| 38 | Roman Hemby | RB | Missing draft-capital context with low evidence, high bust risk, and source-limited warning. |
| 39 | Chase Roberts | WR | Missing draft-capital context with low evidence and source-limited warning. |
| 40 | Barika Kpeenu | RB | Missing draft-capital context with low evidence, high bust risk, and missing CFBD denominator. |
| 41 | Jordan Hudson | WR | Missing draft-capital context with low evidence and source-limited warning. |
| 42 | Kevin Coleman | WR | Missing draft-capital context with low evidence and source-limited warning. |
| 43 | Donaven McCulley | WR | Missing draft-capital context with low evidence, source-limited warning, and no standout CFBD edge. |
| 44 | Caullin Lacy | WR | Missing draft-capital context with low evidence, source-limited warning, and no standout CFBD edge. |
| 45 | Deion Burks | WR | Round 8 profile with low evidence, source-limited warning, no standout CFBD edge, and very late overall pick. |
| 46 | Trebor Pena | WR | Missing draft-capital context with low evidence, source-limited warning, and no standout CFBD edge. |
| 47 | Braylon James | WR | Missing draft-capital context with low evidence, high bust risk, no current CFBD profile, and no standout CFBD edge. |
| 50 | Kaelon Black | RB | Round 3 profile with high bust risk, source-limited warning, and no standout CFBD edge. |
| 51 | Sam Roush | TE | Round 3 profile with low evidence, high bust risk, source-limited warning, and no standout CFBD edge. |
| 52 | Jamal Haynes | RB | Missing draft-capital context with high bust risk, source-limited warning, and no standout CFBD edge. |
| 53 | Jamarion Miller | RB | Missing draft-capital context with high bust risk and no standout CFBD edge. |
| 54 | Chip Trayanum | RB | Missing draft-capital context, low evidence, high bust risk, unmatched current CFBD features, and no standout CFBD edge. |

Not trap-guard flagged: ranks 1-7, Jordyn Tyson at 48, and Eli Stowers at 49. They may still carry existing injury/source/manual warnings; this overlay only answers the narrow draft-capital-trap question.

## Draft-Use Guidance

Use the final overlay board as a manual draft board, not as a production ranking.

Safe use:

- Keep rank order unchanged from `cfbd_enriched_baseline_v1_1`.
- Read the trap-guard column before drafting any top-54 player after the first seven names.
- Treat `hard_manual_review` as an active stop unless Tim can answer the manual question.
- Use `manual_review` as a caution flag, not an automatic downgrade.

Unsafe use:

- Do not use this as a new v2 formula.
- Do not sort the board by trap-guard severity as a hidden rank key.
- Do not hide existing source/injury/manual warnings.
- Do not promote the board into production or app display.
- Do not create probabilities or bands.
- Do not use ADP/market fields as private score inputs.

## Anti-Cheat / Leakage Audit

- Main ranking formula unchanged: PASS
- Rank order unchanged: PASS
- Overlay is warning/manual-review only: PASS
- No new broad tuning weights: PASS
- No v2 board or production ranking: PASS
- ADP/market not used as private input: PASS
- No probabilities or bands: PASS
- No Outcome, app, Streamlit, veteran, hidden sort key, or promoted artifact files touched: PASS

## Validation Commands

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python -m py_compile scripts\rookie_framework\build_draft_capital_trap_guard_overlay.py tests\test_draft_capital_trap_guard_overlay.py`
- `python tests\test_draft_capital_trap_guard_overlay.py`
- `python scripts\rookie_framework\build_draft_capital_trap_guard_overlay.py`
- `python -m pytest tests\test_draft_capital_trap_guard_overlay.py -q`
- `git diff --check`

Result: direct harness and export build passed. `pytest` was unavailable in the active Python environment (`No module named pytest`), so the direct harness result was used.

## Final Recommendation

Use the trap-guard overlay as the final caution layer on top of the current feature-aware draft board. The main formula should stay frozen. The next rookie-only step should be Tim manually clearing or downgrading the hard-manual-review names before draft day, not another broad tuning pass.
