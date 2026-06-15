# Rookie Historical Pool Expansion Audit - 2026-06-15

## Executive Verdict

Historical pool expansion feasibility: GREEN.

Backtest expansion readiness: YELLOW.

Tuning readiness: RED.

Local 2010-2020 historical fantasy/outcome data exists, and a local NFLVERSE draft-pick source exists. A rookie-only audit script produced an 874-row local-only first-three-year label preview for drafted QB/RB/WR/TE players from 2010-2020. That preview is promising enough to proceed to a separate expanded-baseline integration pass, but it is not clean enough to tune yet.

No tuning was performed.

## Files Created

- `scripts/rookie_framework/audit_rookie_historical_pool_expansion_v1.py`
- `tests/test_rookie_historical_pool_expansion_v1.py`
- `docs/rookie_framework/ROOKIE_HISTORICAL_POOL_EXPANSION_AUDIT_20260615.md`

## Local-Only Exports Created

Export directory:

`local_exports/rookie_framework/historical_pool_expansion_audit_20260615/`

Exports:

- `historical_source_inventory_20260615.csv`
- `draft_source_inventory_20260615.csv`
- `historical_pool_join_feasibility_20260615.csv`
- `expanded_label_pool_preview_20260615.csv`
- `README_ROOKIE_HISTORICAL_POOL_EXPANSION_AUDIT_20260615.md`

These exports are local-only and are not committed.

## Source Discovery

2010-2020 historical outcome/fantasy data was found locally.

Primary label-component source:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- Rows: 134,470
- Season coverage: 1999-2024
- Relevant positions present: QB/RB/WR/TE
- Semantics: raw weekly NFL stat components
- Status: GREEN for label reconstruction only

Read-only historical outcome/model-readiness evidence:

- `local_exports/outcome_probability/sprint_5ck_r2_consolidated_2010_2019_historical_model_readiness_reaudit/`
- Consolidated label rows reported: 3,801
- Season coverage: 2010-2019
- Semantics: season-level outcome-probability labels, not first-three-year rookie draft labels
- Status: YELLOW for direct rookie usage; useful as inventory/semantics evidence only

Existing current rookie label baseline:

- `local_exports/rookie_framework/historical_outcome_labels_v1_20260615/rookie_historical_outcome_labels_v1_20260615.csv`
- Rows: 395
- Complete-window rows: 235 from 2021-2023
- Partial/report-only rows: 160 from 2024-2025

Sibling repos were not inspected because the rookie worktree already contained the needed local raw stat, draft, and readiness sources.

## Draft Source / API Audit

Local NFLVERSE draft-pick CSV found:

- `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/nflverse_draft_picks.csv`
- Rows: 12,927
- Year coverage: 1980-2026
- 2010-2020 QB/RB/WR/TE draft rows: 874
- Required fields present: yes
- Stable ID fields present: `gsis_id`, `pfr_player_id`, `cfb_player_id`
- Draft capital fields present: `round`, `pick`

No package install or network download was needed.

Important draft-source quarantine:

The local draft-pick file includes career outcome fields such as `hof`, `allpro`, `probowls`, `seasons_started`, `w_av`, `car_av`, `dr_av`, `games`, and career passing/rushing/receiving totals. These must be allowlist-excluded from any feature builder. The source is safe only as an identity/draft-capital source after explicit column allowlisting.

## Label Semantics

The safe expansion path is to reconstruct labels from raw stat components in `player_stats.csv`, not to directly consume Outcome probability season heads.

Preview label semantics:

- Year 1, year 2, and year 3 fantasy points after draft year
- First-three-year total points
- Best first-three-year season points
- Best first-three-year positional rank
- Starter seasons
- Star/useful/bust flags

Scoring:

- Passing yards: 1 per 30
- Passing TD: 3
- Interception: -1
- Rush/receiving yards: 1 per 10
- Rush/receiving TD: 4
- Rush/receiving first downs: 0.4
- Return yards: included only when source columns exist
- Special teams TD: 4
- Two-point conversions: 2
- Fumbles lost: -1

Known scoring caveat:

The 2010-2020 preview is marked `exact_non_ppr_with_rush_rec_first_downs_return_yards_partial_pre_2025` because return-yard column availability is incomplete before the newer 2025 source. The labels are useful for audit/backtest expansion but need QA before tuning.

## Join Feasibility By Year

The audit preview joined draft identity to stat labels by normalized player name, position, and first-three-year seasons. Stable IDs are present in the draft source and should be used or retained in the next integration pass where possible.

| Draft year | Drafted QB/RB/WR/TE rows | Preview labels | Any stat match | Assumed-zero/no stat | Status |
|---|---:|---:|---:|---:|---|
| 2010 | 78 | 78 | 65 | 13 | GREEN_PREVIEW_LABELABLE |
| 2011 | 82 | 82 | 71 | 11 | GREEN_PREVIEW_LABELABLE |
| 2012 | 77 | 77 | 66 | 11 | GREEN_PREVIEW_LABELABLE |
| 2013 | 80 | 80 | 66 | 14 | GREEN_PREVIEW_LABELABLE |
| 2014 | 77 | 77 | 60 | 17 | GREEN_PREVIEW_LABELABLE |
| 2015 | 79 | 79 | 65 | 14 | GREEN_PREVIEW_LABELABLE |
| 2016 | 77 | 77 | 62 | 15 | GREEN_PREVIEW_LABELABLE |
| 2017 | 83 | 83 | 69 | 14 | GREEN_PREVIEW_LABELABLE |
| 2018 | 83 | 83 | 72 | 11 | GREEN_PREVIEW_LABELABLE |
| 2019 | 80 | 80 | 70 | 10 | GREEN_PREVIEW_LABELABLE |
| 2020 | 78 | 78 | 73 | 5 | GREEN_PREVIEW_LABELABLE |

Preview totals:

- 874 complete-window 2010-2020 rows
- 739 rows with at least one stat-season match
- 135 assumed-zero/no-stat rows
- 0 duplicate preview keys
- 94 star flags
- 373 bust flags

Estimated complete-window pool after expansion:

- Current 2021-2023 complete-window rows: 235
- Preview 2010-2020 complete-window rows: 874
- Estimated expanded complete-window pool: 1,109 rows before alias/ID QA

## Why Backtest Expansion Is Still YELLOW

Backtest expansion should not run immediately as a tuning input because:

- The draft source contains career outcome fields that require strict allowlisting.
- 135 assumed-zero rows need alias/identity review before treating them as true zero outcomes.
- The preview join used normalized name + position; the next pass should prefer stable IDs or retain ID-backed audit columns.
- The Outcome probability 2010-2019 labels are season-level outcome heads, not first-three-year rookie draft labels.
- Return-yard scoring is partial for pre-2025 source rows.

These are repairable blockers, not source-discovery failures.

## Expanded Baseline

Expanded baseline was not run.

Reason: the task was pool expansion audit, and backtest readiness is YELLOW until alias/ID QA and draft-source allowlisting are completed. No model tuning or candidate board generation occurred.

## Anti-Cheat / Leakage Audit

- PASS: No player-specific boosts or penalties were added.
- PASS: Names, aliases, player IDs, schools, teams, and years are used only for identity, display, grouping, duplicate detection, and deterministic audit keys.
- PASS: Outcome labels are used only as evaluation labels.
- PASS: ADP, market, public rankings, projections, and trade calculators are not used as private score inputs.
- PASS: Future NFL stats are not used as pre-draft features.
- PASS: Sibling/outcome data was not modified and was not used as a private model input.
- PASS: Draft source career outcome columns are explicitly quarantined.
- PASS: No production rankings, private scores, outcome columns, app wiring, Streamlit files, veteran files, probabilities, bands, hidden sort keys, or promoted artifacts were touched.
- PASS: `data/` and `local_exports/` were not committed.

## Validation Commands

- `git status --short`
- `git branch --show-current`
- `git log --oneline -10`
- `git diff --check`
- `python -m py_compile scripts/rookie_framework/audit_rookie_historical_pool_expansion_v1.py`
- `python scripts/rookie_framework/audit_rookie_historical_pool_expansion_v1.py`
- `python tests/test_rookie_historical_pool_expansion_v1.py`
- existing strict rookie builders
- existing direct rookie harnesses
- `python -m pytest tests/test_rookie_historical_pool_expansion_v1.py -q`

Pytest is unavailable locally: `No module named pytest`.

## Recommended Next Safe Step

Run a rookie-only historical pool expansion integration repair pass:

1. Create a strict draft-pick source allowlist that excludes all career outcome columns.
2. Add alias/ID QA for the 135 assumed-zero preview rows.
3. Promote the preview into a local-only expanded label package only after QA.
4. Run an expanded baseline on 2010-2023 complete-window rows.
5. Do not tune until expanded baseline metrics are reviewed.
