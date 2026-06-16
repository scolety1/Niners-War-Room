# Rookie Current 2026 Feature-Aware Board Sanity Audit

Date: 2026-06-15

Lane: Rookie framework only

## Executive Verdict

- Board sanity: YELLOW
- Draft-use readiness: YELLOW
- Manual draft trust: YELLOW
- Anti-cheat/leakage: GREEN

The current 2026 feature-aware candidate board is coherent enough for manual draft review, but it is not production-ready and should not be used as a blind ranking. The top of the board is RB/WR-heavy, which is sane for Tim's 10-team, 1QB, non-PPR, 0.4 rush/rec first-down dynasty/keeper format. The board still needs visible manual review because 31 of the top 36 rows carry manual-review/source/injury flags.

No tuning was performed. No production ranking, private score, app wiring, Streamlit file, Outcome file, veteran file, probability, band, hidden sort key, or promoted artifact was created.

## Files Created

- `scripts/rookie_framework/audit_current_2026_feature_aware_board_sanity.py`
- `tests/test_current_2026_feature_aware_board_sanity.py`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_BOARD_SANITY_AUDIT_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/current_2026_board_sanity_audit_20260615/`:

- `current_2026_board_top12_20260615.csv`
- `current_2026_board_top24_20260615.csv`
- `current_2026_board_top36_20260615.csv`
- `current_2026_position_top_lists_20260615.csv`
- `current_2026_focus_player_sanity_20260615.csv`
- `current_2026_unmatched_neutral_rows_20260615.csv`
- `current_2026_top36_manual_review_flags_20260615.csv`
- `current_2026_clean_draft_use_sheet_20260615.csv`
- `current_2026_position_balance_sanity_20260615.csv`
- `current_2026_board_sanity_verdicts_20260615.csv`
- `README_CURRENT_2026_BOARD_SANITY_AUDIT_20260615.md`

These exports are local-only and were not committed.

## Top 12 Summary

| Rank | Old | Player | Pos | Delta | Feature Reason | Manual Review |
|---:|---:|---|---|---:|---|---|
| 1 | 1 | Jeremiyah Love | RB | 0 | elite CFBD production plus strong share | manual/source/injury review |
| 2 | 3 | Makai Lemon | WR | +1 | elite CFBD production plus strong share | manual/source review |
| 3 | 21 | Carnell Tate | WR | +18 | strong CFBD production | manual/source/injury review |
| 4 | 2 | KC Concepcion | WR | -2 | strong CFBD production | manual/source review |
| 5 | 6 | Jadarian Price | RB | +1 | fixed formula blend; no standout CFBD edge | manual/source/injury review |
| 6 | 4 | Denzel Boston | WR | -2 | strong CFBD production | manual/source review |
| 7 | 5 | Germie Bernard | WR | -2 | strong CFBD production | manual/source review |
| 8 | 8 | Chris Bell | WR | 0 | elite CFBD production plus strong share | manual/source review |
| 9 | 7 | Zachariah Branch | WR | -2 | strong CFBD production | manual/source review |
| 10 | 46 | Antonio Williams | WR | +36 | fixed formula blend; no standout CFBD edge | manual/source/injury review |
| 11 | 35 | Jonah Coleman | RB | +24 | strong CFBD production | manual/source/injury review |
| 12 | 13 | Skyler Bell | WR | +1 | elite CFBD production plus strong share | manual/source review |

## Top 24 Summary

Position mix:

- RB: 10
- WR: 14
- TE: 0
- QB: 0

Entered top 24:

- Antonio Williams
- Jonah Coleman
- Barion Brown
- Kentrel Bullock

Left top 24:

- Jordyn Tyson
- Hank Beatty
- Chase Roberts
- Donaven McCulley

Sanity verdict: YELLOW. The RB/WR mix is plausible for Tim's scoring format, but the top 24 has many source-limited/manual rows. Use as a draft review board, not as an autopick list.

## Top 36 Summary

Position mix:

- RB: 15
- WR: 21
- TE: 0
- QB: 0

Top 36 balance verdict: GREEN for 10-team 1QB non-PPR first-down scoring. The board does not overpush rookie QBs or TEs into the premium window. The RB/WR concentration is reasonable.

Manual-review caveat: 31 of the top 36 carry manual-review/source/injury flags. Clean draft use requires reading the warning column, not just the rank.

## Biggest Risers

Focus-player risers:

- Carnell Tate: 21 to 3. Strong source-safe CFBD production pushed him into the premium tier, but he remains manual/source/injury review before draft use.
- Antonio Williams: 46 to 10. Enters top 12 on the fixed formula blend; because the audit did not see a standout CFBD edge, this is a manual-review riser, not a slam-dunk promotion.
- Jonah Coleman: 35 to 11. Strong RB CFBD production/share improves him for first-down/non-PPR context; still manual/source/injury review.
- Barion Brown: 52 to 20. Enters top 24 with matched WR production context; still manual/source/injury review.
- Kentrel Bullock: 41 to 24. Enters top 24 with strong RB production context; still source/injury review.

Large non-premium risers outside the draft-use tier are mostly QBs with strong CFBD production/share. In a 1QB league, those should not be overread.

## Biggest Fallers

Focus-player fallers:

- Jordyn Tyson: 19 to 48. Leaves top 24 and remains a major manual-review case because injury review was already a known blocker.
- Hank Beatty: 20 to 35. Falls but stays top 36; no extra manual flag beyond visible warnings.
- Chase Roberts: 23 to 39. Leaves top 36; source-limited profile.
- Donaven McCulley: 24 to 43. Leaves top 36; source-limited profile.

Unmatched fallers:

- Mike Washington: 57 to 182.
- Jam Miller: 82 to 183.
- Jaydn Ott: 114 to 184.
- DJ Rogers: 138 to 211.

Those fall because unmatched current CFBD rows remain neutral, not because missing data was treated as bad production.

## Unmatched / Neutral Rows

Unmatched rows are warning-visible and neutral for CFBD context. They are not zero-filled as bad production.

| Player | Pos | Old Rank | Candidate Rank | Treatment |
|---|---|---:|---:|---|
| Chip Trayanum | RB | 54 | 181 | neutral CFBD context; manual review |
| Mike Washington | RB | 57 | 182 | neutral CFBD context; unavailable warning |
| Reggie Virgil | WR | 74 | 188 | neutral CFBD context; unavailable warning |
| Jam Miller | RB | 82 | 183 | neutral CFBD context; unavailable warning |
| Jaydn Ott | RB | 114 | 184 | neutral CFBD context; unavailable warning |
| DJ Rogers | TE | 138 | 211 | neutral CFBD context; unavailable warning |
| Ja'Mori Maclin | WR | 148 | 189 | neutral CFBD context; unavailable warning |
| Ryan Niblett | WR | 165 | 200 | neutral CFBD context; unavailable warning |

None of these players are in the top 36 candidate board.

## Manual Review Before Draft Use

Top-36 players that should be manually reviewed before draft use: 31.

Common reasons:

- manual evidence flags remain
- source-limited profile
- injury review before draft use

Notable premium manual-review rows:

- Jeremiyah Love
- Makai Lemon
- Carnell Tate
- KC Concepcion
- Jadarian Price
- Denzel Boston
- Germie Bernard
- Chris Bell
- Zachariah Branch
- Antonio Williams
- Jonah Coleman

The clean draft sheet keeps these warnings attached.

## Clean Draft Sheet

Created:

- `current_2026_clean_draft_use_sheet_20260615.csv`

Rows: 54

Included columns:

- overall rank
- position rank
- player
- position
- draft action
- feature reason
- warning/manual-review reason
- unmatched/neutral flag

This sheet is local/manual-use only. It is not production-ready and is not app-readable.

## Draft-Use Recommendation

Use the feature-aware board as a manual advisory board with warnings visible. It is more useful than the previous board because rank movement is now tied to source-safe CFBD production/share context, but it remains YELLOW because premium rows still require manual review.

Practical use:

- Treat top 12 as the premium review pool.
- Treat top 24 as the draft-window pool.
- Treat top 36 as the watch/value pool.
- Do not draft Jordyn Tyson without resolving injury review.
- Do not elevate unmatched rows without identity/feature repair.
- Do not use QB risers as premium targets in this 1QB format.

## Anti-Cheat / Leakage Audit

- PASS: no tuning occurred.
- PASS: no new weights were created.
- PASS: no ADP, market, public rankings, projections, consensus, trade values, or draft-kit ranks were used as private score inputs.
- PASS: no probabilities or bands were created.
- PASS: no app/Streamlit/production wiring was created.
- PASS: no Outcome files, outcome columns, veteran files, private scores, hidden sort keys, or promoted artifacts were touched.
- PASS: no API keys or secrets were printed, exported, or committed.
- PASS: local exports remain uncommitted.
- PASS: `data/` remains uncommitted.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `python -m py_compile scripts\rookie_framework\audit_current_2026_feature_aware_board_sanity.py tests\test_current_2026_feature_aware_board_sanity.py`
- `python tests\test_current_2026_feature_aware_board_sanity.py`
- `python scripts\rookie_framework\audit_current_2026_feature_aware_board_sanity.py`
- `python scripts\rookie_framework\build_rookie_review_board_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_shadow_ranking_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_production_candidate_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_analyzer_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_day_simulation_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_ranking_v01.py`
- `python scripts\rookie_framework\build_current_2026_cfbd_feature_ingestion.py`
- `python scripts\rookie_framework\build_current_2026_feature_aware_rescore_candidate.py`
- `python tests\test_current_2026_feature_aware_rescore_candidate.py`
- `python tests\test_current_2026_cfbd_feature_ingestion.py`
- `python -m pytest tests\test_current_2026_feature_aware_board_sanity.py -q`
- `Select-String -Path scripts\rookie_framework\audit_current_2026_feature_aware_board_sanity.py -Pattern 'api_key|CFBD_API|private_score|probability|band|streamlit|outcome_probability|hidden sort|adp|market|if\s+.*player_name\s*==' -CaseSensitive:$false`

Pytest was unavailable: `No module named pytest`. Direct harnesses passed. Safety-scan hits were limited to source-safe CFBD market-share field names and guardrail text; no ADP/private-market scoring, secret values, player-specific tuning, probabilities, bands, hidden sort keys, app wiring, or Outcome references were found.

## Recommended Next Rookie-Only Task

Use the clean draft-use sheet for Tim review, then run a final manual draft checklist pass focused on premium picks 1.03 and 1.04 before making any live draft decision.
