# Rookie Current 2026 Feature-Aware Rescore Candidate

Date: 2026-06-15

Lane: Rookie framework only

## Executive Verdict

- Rescore quality: YELLOW
- Ranking usefulness: YELLOW
- Manual draft trust: YELLOW
- Anti-cheat/leakage: GREEN

Created a local/manual-use feature-aware rookie draft ranking candidate using the fixed historically supported `cfbd_enriched_baseline_v1_1` formula. No new weights were tuned.

This is not production-ready. It is not app-readable. It is not a promoted ranking. It is a manual draft-use candidate board for review only.

## Inputs

- `docs/rookie_framework/ROOKIE_CURRENT_2026_CFBD_FEATURE_INGESTION_20260615.md`
- `local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/current_2026_feature_ingested_manual_board_20260615.csv`
- `local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615/current_2026_cfbd_feature_coverage_by_position_20260615.csv`
- `scripts/rookie_framework/tune_rookie_model_runway_v1_1.py`

## Files Created

- `scripts/rookie_framework/build_current_2026_feature_aware_rescore_candidate.py`
- `tests/test_current_2026_feature_aware_rescore_candidate.py`
- `docs/rookie_framework/ROOKIE_CURRENT_2026_FEATURE_AWARE_RESCORE_CANDIDATE_20260615.md`

## Local-Only Exports

Created under `local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/`:

- `current_2026_feature_aware_candidate_board_20260615.csv`
- `current_2026_feature_aware_rank_movement_20260615.csv`
- `current_2026_feature_aware_top24_old_vs_new_20260615.csv`
- `current_2026_feature_aware_unmatched_policy_20260615.csv`
- `current_2026_feature_aware_coverage_by_position_20260615.csv`
- `current_2026_source_ingestion_coverage_reference_20260615.csv`
- `README_CURRENT_2026_FEATURE_AWARE_RESCORE_CANDIDATE_20260615.md`

These exports are local-only and were not committed.

## Model Applied

Model: `cfbd_enriched_baseline_v1_1`

Fixed formula weights:

- draft weight: 0.68
- position weight: 0.20
- CFBD production weight: 0.07
- CFBD market-share weight: 0.05
- scoring-fit weight: 0.00

Position anchors:

- RB: 72
- WR: 70
- TE: 42
- QB: 24

No new weights were tuned in this task.

## Safety Ordering

Rows are ordered by safety bucket first, then by feature-aware score:

1. `rankable_with_warning`
2. `manual_review_required`
3. `blocked`
4. `unavailable`

This preserves the existing warning/status logic so blocked or unavailable players cannot jump over draftable warning rows only because they have strong CFBD production.

## Current Feature Coverage

| Position | Rows | Matched | Unmatched | Denominator Ready | Match Rate | Denominator Rate |
|---|---:|---:|---:|---:|---:|---:|
| QB | 34 | 34 | 0 | 32 | 1.000 | 0.941 |
| RB | 46 | 42 | 4 | 38 | 0.913 | 0.826 |
| WR | 90 | 87 | 3 | 83 | 0.967 | 0.922 |
| TE | 41 | 40 | 1 | 40 | 0.976 | 0.976 |

## Unresolved / Unmatched Policy

Unmatched rows are not zero-filled as bad production. They receive neutral CFBD context and remain warning-visible with `CFBD_UNMATCHED_CURRENT_IDENTITY`.

Unmatched rows:

| Old Rank | Candidate Rank | Player | Position | School | Policy |
|---:|---:|---|---|---|---|
| 54 | 181 | Chip Trayanum | RB | Toledo | unmatched neutral CFBD context |
| 57 | 182 | Mike Washington | RB | Arkansas | unmatched neutral CFBD context |
| 74 | 188 | Reggie Virgil | WR | Texas Tech | unmatched neutral CFBD context |
| 82 | 183 | Jam Miller | RB | Alabama | unmatched neutral CFBD context |
| 114 | 184 | Jaydn Ott | RB | Oklahoma | unmatched neutral CFBD context |
| 138 | 211 | DJ Rogers | TE | TCU | unmatched neutral CFBD context |
| 148 | 189 | Ja'Mori Maclin | WR | Kentucky | unmatched neutral CFBD context |
| 165 | 200 | Ryan Niblett | WR | Texas | unmatched neutral CFBD context |

## Old vs New Top 24

Old top 24 position mix:

- RB: 8
- WR: 16

Feature-aware candidate top 24 position mix:

- RB: 10
- WR: 14

Entered top 24:

- Antonio Williams, WR
- Jonah Coleman, RB
- Barion Brown, WR
- Kentrel Bullock, RB

Left top 24:

- Jordyn Tyson, WR
- Hank Beatty, WR
- Chase Roberts, WR
- Donaven McCulley, WR

Top candidate rows:

| Candidate Rank | Old Rank | Player | Pos | Score | Production | Market Share | Note |
|---:|---:|---|---|---:|---:|---:|---|
| 1 | 1 | Jeremiyah Love | RB | 91.576 | 91.067 | 61.117 | strong RB production/share; status remains warning-visible |
| 2 | 3 | Makai Lemon | WR | 89.160 | 89.673 | 51.663 | strong WR production/share |
| 3 | 21 | Carnell Tate | WR | 88.787 | 77.733 | 33.705 | major riser from source-safe CFBD production |
| 4 | 2 | KC Concepcion | WR | 87.995 | 83.587 | 43.683 | still premium, small move down within strong top tier |
| 5 | 6 | Jadarian Price | RB | 85.230 | 57.669 | 30.273 | RB production keeps him near top |
| 6 | 4 | Denzel Boston | WR | 75.236 | 75.632 | 42.742 | still premium; slightly lower than top CFBD profiles |
| 7 | 5 | Germie Bernard | WR | 73.822 | 73.328 | 31.276 | still premium; slightly lower market-share profile |
| 8 | 8 | Chris Bell | WR | 61.739 | 81.600 | 48.331 | holds top 10 with strong production/share |

## Biggest Risers

The largest absolute movers are mostly outside the top draft-use tier because status buckets still apply.

| Player | Pos | Old Rank | Candidate Rank | Delta | Explanation |
|---|---|---:|---:|---:|---|
| Jake Retzlaff | QB | 207 | 75 | +132 | strong CFBD market-share/dominator component, but still below draftable warning rows by status bucket |
| Thomas Castellanos | QB | 206 | 76 | +130 | strong CFBD production/share, but not a premium 1QB draft target |
| Mark Gronowski | QB | 209 | 86 | +123 | strong CFBD share context, still status-limited |
| Owen McCown | QB | 204 | 82 | +122 | strong CFBD production/share, still status-limited |
| Haynes King | QB | 194 | 73 | +121 | strong CFBD market-share/dominator component, still status-limited |
| Jalon Daniels | QB | 195 | 74 | +121 | strong CFBD market-share/dominator component, still status-limited |

Draft-use top-24 risers:

- Carnell Tate: +18, strong source-safe CFBD production.
- Antonio Williams: +36, enters top 24 on matched WR production/share.
- Jonah Coleman: +24, enters top 24 with strong RB production/share.
- Barion Brown: +32, enters top 24 with matched WR production context.
- Kentrel Bullock: +17, enters top 24 with matched RB production context.

## Biggest Fallers

| Player | Pos | Old Rank | Candidate Rank | Delta | Explanation |
|---|---|---:|---:|---:|---|
| Mike Washington | RB | 57 | 182 | -125 | unmatched current CFBD row; CFBD context stayed neutral and warning-visible |
| Dallen Bentley | TE | 71 | 190 | -119 | lower fixed-formula CFBD/draft/position blend relative to peers |
| Jam Miller | RB | 82 | 183 | -101 | unmatched current CFBD row; CFBD context stayed neutral and warning-visible |
| Dan Villari | TE | 113 | 199 | -86 | lower fixed-formula CFBD/draft/position blend relative to peers |
| Michael Trigg | TE | 106 | 185 | -79 | lower fixed-formula CFBD/draft/position blend relative to peers |

Draft-use top-24 fallers:

- Jordyn Tyson leaves top 24. This should be reviewed manually because earlier packets flagged injury review as important.
- Hank Beatty leaves top 24.
- Chase Roberts leaves top 24.
- Donaven McCulley leaves top 24.
- J'Mari Taylor drops from 14 to 23 but remains top 24.

## Is This Safer Than The Previous Board?

Verdict: YELLOW, useful but not authoritative.

Safer:

- Current CFBD production/share context is now attached to rank movement.
- Unmatched rows are visible and not treated as bad production.
- Warning/status buckets prevent blocked or unavailable players from jumping over draftable rows.
- ADP/market fields remain display-only and unused.

Still risky:

- The formula was historically supported, but it was not revalidated specifically as a current 2026 draft board.
- Some large moves are outside the top draft-use tier and should not be overread.
- Injury and manual scouting flags still matter, especially for premium rows.
- This should guide manual review, not replace it.

## Candidate Board Decision

Local/manual-use candidate board created: yes

Production board created: no

App wiring created: no

Probabilities or bands created: no

## Anti-Cheat / Leakage Audit

- PASS: no new weights were tuned.
- PASS: no player-name, player-ID, school, team, class, or known-outcome tuning rules were added.
- PASS: ADP/market/public rankings/projections/consensus/trade values were not used as private score inputs.
- PASS: CFBD rows are factual regular-season production and team denominator context.
- PASS: unmatched rows are neutral CFBD context, not zero-filled bad production.
- PASS: warning/manual-review flags remain visible.
- PASS: no Outcome files, production rankings, private scores, outcome columns, app wiring, Streamlit files, veteran files, probabilities, bands, hidden sort keys, or promoted artifacts were touched.
- PASS: no secret was printed, exported, or committed.

## Commands Run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `python -m py_compile scripts\rookie_framework\build_current_2026_feature_aware_rescore_candidate.py tests\test_current_2026_feature_aware_rescore_candidate.py`
- `python tests\test_current_2026_feature_aware_rescore_candidate.py`
- `python scripts\rookie_framework\build_current_2026_feature_aware_rescore_candidate.py`
- `python scripts\rookie_framework\build_rookie_review_board_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_shadow_ranking_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_production_candidate_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_analyzer_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_day_simulation_v03.py --strict`
- `python scripts\rookie_framework\build_rookie_draft_ranking_v01.py`
- `python scripts\rookie_framework\build_rookie_historical_outcome_labels_v1.py`
- `python scripts\rookie_framework\backtest_rookie_ranking_model_v01.py`
- `python scripts\rookie_framework\build_current_2026_cfbd_feature_ingestion.py`
- `python scripts\rookie_framework\build_rookie_cfbd_historical_feature_cache_v1.py --skip-fetch`
- `python scripts\rookie_framework\audit_rookie_cfbd_identity_join_repair_v1.py`
- `python tests\test_current_2026_cfbd_feature_ingestion.py`
- `python tests\test_rookie_wr_feature_quality_pass_20260615.py`
- `python tests\test_rookie_model_tuning_runway_v1_1.py`
- `python -m pytest tests\test_current_2026_feature_aware_rescore_candidate.py -q`
- `Select-String -Path scripts\rookie_framework\build_current_2026_feature_aware_rescore_candidate.py -Pattern 'api_key|CFBD_API|if\s+.*player|player_name\s*==|private_score|probability|band|streamlit|outcome_probability|hidden sort|adp|market' -CaseSensitive:$false`

Pytest was unavailable: `No module named pytest`. Direct harnesses passed. Safety-scan hits were limited to guardrail text, generic player-id membership checks, and source-safe CFBD market-share component names; no secret values, ADP/private-value use, or player-specific tuning rules were found.

## Recommended Next Rookie-Only Task

Run a manual top-24 review packet comparing the old board, feature-aware candidate board, and injury/manual scouting flags before using the candidate board live.
