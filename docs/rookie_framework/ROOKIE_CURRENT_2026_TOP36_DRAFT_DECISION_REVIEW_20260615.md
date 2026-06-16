# Rookie Current 2026 Top-36 Draft Decision Review

Date: 2026-06-15

Lane: Rookie framework only

## Executive Verdict

- Draft-use clarity: GREEN
- Manual-review burden: YELLOW
- Ranking trust: YELLOW
- Anti-cheat/leakage: GREEN
- Draft-day usability: YES, with manual review visible

This packet converts the current 2026 feature-aware draft-use sheet into manual draft actions for Tim. It is not tuning, not production, and not an app ranking. The board is usable as a draft-day advisory sheet only if the warning/manual-review questions stay attached to the ranks.

No production ranking, private score, app wiring, Streamlit file, Outcome file, veteran file, probability, band, hidden sort key, or promoted artifact was created.

## Inputs Reviewed

- `docs/rookie_framework/ROOKIE_CURRENT_2026_FEATURE_AWARE_RESCORE_CANDIDATE_20260615.md`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_BOARD_SANITY_AUDIT_20260615.md`
- `local_exports/rookie_framework/current_2026_board_sanity_audit_20260615/current_2026_clean_draft_use_sheet_20260615.csv`
- `local_exports/rookie_framework/current_2026_board_sanity_audit_20260615/current_2026_board_top36_20260615.csv`
- `local_exports/rookie_framework/current_2026_board_sanity_audit_20260615/current_2026_focus_player_sanity_20260615.csv`
- `local_exports/rookie_framework/current_2026_board_sanity_audit_20260615/current_2026_unmatched_neutral_rows_20260615.csv`

## Files Created

- `scripts/rookie_framework/build_current_2026_top36_draft_decision_review.py`
- `tests/test_current_2026_top36_draft_decision_review.py`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/current_2026_top36_draft_decision_review_20260615/`:

- `top36_draft_decision_review_20260615.csv`
- `top36_tiers_20260615.csv`
- `top_manual_review_questions_20260615.csv`
- `focus_player_decision_review_20260615.csv`
- `unmatched_relevant_names_review_20260615.csv`
- `draft_day_decision_sheet_20260615.csv`
- `decision_review_verdicts_20260615.csv`
- `README_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md`

These exports are local-only and must not be committed.

## Tim Draft Tiers

### Tier 1: Priority Targets

- Jeremiyah Love
- Makai Lemon
- Carnell Tate
- KC Concepcion
- Jadarian Price
- Denzel Boston
- Germie Bernard
- Chris Bell
- Zachariah Branch

Use these as the premium target pool, but not as automatic picks. Every Tier 1 row still has visible review context.

### Tier 2: Strong Considers

- Antonio Williams
- Jonah Coleman
- Skyler Bell
- Brenen Thompson
- Elijah Sarratt
- Emmett Johnson
- Kaytron Allen
- Adam Randall
- Josh Cameron
- Nicholas Singleton
- Barion Brown
- Demond Claiborne
- Lewis Bond
- J'Mari Taylor
- Kentrel Bullock

Use these as strong draft-window alternatives if Tier 1 dries up or if Tim prefers the role/first-down fit.

### Tier 3: Value/Fit Targets

- Eric McAlister
- Kejon Owens
- Sieh Bangura
- Chris Brazzell
- Robert Henry Jr.
- Seth McGowan
- Jacob De Jesus
- Omar Cooper
- Dominic Richardson
- Devin Voisin
- Hank Beatty
- O'Mega Blake

These are draftable as value/fit targets, especially if the draft room lets them slide. They should not be pushed above premium target/strong-consider names without a manual reason.

### Tier 4: Manual-Review Upside

- Chase Roberts
- Donaven McCulley
- Jordyn Tyson

These are not top-36 model-cleared picks today. They can be considered only if Tim resolves the specific manual warning and prefers the upside over safer top-36 alternatives.

### Tier 5: Avoid/Hold Unless Price Drops

- Chip Trayanum
- Reggie Virgil
- Mike Washington
- Jam Miller
- Jaydn Ott
- Ja'Mori Maclin
- Ryan Niblett
- DJ Rogers

These names are not model-cleared because current CFBD identity/feature evidence is unmatched or unavailable in the current feature path. Do not draft them from the model alone.

## Focus Player Decisions

| Player | Rank | Action | Clearance | Main Decision |
|---|---:|---|---|---|
| Carnell Tate | 3 | target | draftable only with review | Confirm injury/source review is clean enough for premium cost. |
| Antonio Williams | 10 | target | draftable only with review | Confirm injury/source review and role support before treating him as a top-12 target. |
| Jonah Coleman | 11 | target | draftable only with review | Confirm injury/source review and RB role stability. |
| Barion Brown | 20 | consider | draftable only with review | Confirm injury/source review before using as a top-24 pick. |
| Kentrel Bullock | 24 | consider | draftable only with review | Confirm injury/source review and RB role path. |
| Hank Beatty | 35 | wait | safe from model | Decide whether Tim actively prefers him over nearby top-36 alternatives. |
| Chase Roberts | 39 | wait | draftable only with review | Source-limited profile; use only if film/role evidence supports the upside. |
| Donaven McCulley | 43 | wait | draftable only with review | Source-limited profile; use only if film/role evidence supports the upside. |
| Jordyn Tyson | 48 | manual hold | draftable only with review | Injury/source review must be resolved before draft use. |
| Jam Miller | 183 | avoid | not model-cleared | Missing/unmatched evidence must be repaired before considering. |
| Jaydn Ott | 184 | avoid | not model-cleared | Missing/unmatched evidence must be repaired before considering. |

## Top Manual-Review Questions

1. Are the Tier 1 injury/source flags resolved enough to use those players at premium pick cost?
2. Does Carnell Tate's production profile remain strong after injury/source review, or should he slide behind safer Tier 1 names?
3. Are Antonio Williams, Jonah Coleman, Barion Brown, and Kentrel Bullock supported by enough role/film evidence to treat their feature-aware moves as actionable?
4. Is Jordyn Tyson's injury review fully resolved? If not, keep him on manual hold.
5. Are Chase Roberts and Donaven McCulley source-limited upside stashes only, rather than top-36 targets?
6. Are Jam Miller and Jaydn Ott still unmatched/unavailable in the current CFBD path? If yes, do not use the model to draft them.
7. Does Tim prefer Hank Beatty's WR value/fit profile over nearby Tier 3 names, or should he wait?

## Draft-Day Use Guidance

The board is usable for draft day as a manual advisory board. Use the ranks to organize the conversation, then use the action and manual question columns before each pick.

Safe use:

- Use Tier 1 and Tier 2 as the primary board.
- Keep all warning/manual-review text visible.
- Treat Tier 4 as upside-only, not as model-cleared top-36 value.
- Treat Tier 5 as avoid/hold until missing evidence is repaired.
- Do not treat the board as production-ready or app-ready.

Unsafe use:

- Do not autopick by rank.
- Do not hide injury/source/manual flags.
- Do not promote this board into production rankings.
- Do not use ADP, market, consensus, projections, or public rankings as private score inputs.
- Do not create probabilities or bands.
- Do not use veteran outcome heads.

## Anti-Cheat / Leakage Audit

- Player names/IDs were used only for display, focus-player diagnostics, and manual-review grouping: PASS
- No player-specific scoring boost or penalty was added: PASS
- No tuning or rescoring was performed: PASS
- ADP/market fields were not used as private inputs: PASS
- Outcome labels were not used: PASS
- No probabilities or bands were created: PASS
- No production/app/Streamlit/veteran/Outcome files were touched: PASS

## Validation Commands

- `git status --short`
- `git branch --show-current`
- `python -m py_compile scripts\rookie_framework\build_current_2026_top36_draft_decision_review.py tests\test_current_2026_top36_draft_decision_review.py`
- `python tests\test_current_2026_top36_draft_decision_review.py`
- `python scripts\rookie_framework\build_current_2026_top36_draft_decision_review.py`
- `git diff --check`
- `python scripts\rookie_framework\build_rookie_review_board_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_shadow_ranking_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_production_candidate_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_analyzer_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_day_simulation_v03.py --strict`
- `python -m pytest tests\test_current_2026_top36_draft_decision_review.py -q`

Result: strict builders and direct harnesses passed. `pytest` was unavailable in the active Python environment (`No module named pytest`), so the direct harness result was used.

## Final Recommendation

Use this packet as Tim's draft-day decision layer for the current board. The board is usable after this review, but only as a manual advisory board with warnings visible. The next rookie-only task should be either a final Tim pre-draft confirmation pass on the Tier 1/Tier 2 injury and source flags, or a narrow CFBD identity repair for Tier 5 unmatched names if Tim wants those players reconsidered.
