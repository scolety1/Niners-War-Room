# Rookie CFBD-Enriched Tuning Candidate Audit v1 - 2026-06-15

## Executive verdict

Phase B ran because Phase A gates passed.

Verdicts:

| Area | Verdict |
| --- | --- |
| Tuning result | YELLOW |
| Candidate quality | YELLOW |
| Manual draft trust | YELLOW |
| Anti-cheat / leakage | GREEN |
| V2 board creation | no |

Best audit candidate: `scoring_format_fit_plus`.

The best candidate improved 2022-2023 validation Top 12 star capture and reduced validation bust rates versus the CFBD-enriched baseline. It also improved WR position Top 24 star capture in the full position view. Still, no v2 candidate board was created because 127 unresolved complete-window rows and 8 duplicate-selected rows remain warning/manual-review issues, and validation WR Top 12 remains fragile.

## Split and scope

Split:

- train: 2010-2021 complete-window rows;
- validation: 2022-2023 complete-window rows;
- 2024-2025 partial-window rows: excluded.

Candidate logic used general feature-family weights only:

- draft capital;
- position calibration;
- CFBD production/share component;
- broad RB/WR/TE/QB family adjustments;
- broad round guardrails.

No candidate used player names, IDs, schools, NFL teams, exact draft years, ADP, market values, projections, public rankings, future stats, or known outcomes as scoring features.

## Candidate decisions

| Candidate | Decision | Validation Top 12 star delta | Validation Top 24 star delta | Validation Top 12 bust delta | Validation Top 24 bust delta |
| --- | --- | ---: | ---: | ---: | ---: |
| `cfbd_production_plus` | fail | -0.063 | 0.000 | 0.000 | -0.021 |
| `wr_market_share_upside_plus` | fail | -0.063 | 0.000 | 0.041 | 0.000 |
| `scoring_format_fit_plus` | pass for audit | 0.063 | 0.000 | -0.042 | -0.021 |
| `draft_capital_trap_guard` | fail | -0.063 | 0.000 | 0.000 | -0.021 |
| `position_calibrated_cfbd` | fail | 0.000 | 0.000 | 0.041 | -0.042 |
| `balanced_star_bust_cfbd` | fail | -0.063 | 0.000 | 0.041 | -0.021 |

## Baseline vs best candidate

Validation split: 2022-2023.

| Model | Bucket | Stars | Star capture | Bust rate |
| --- | --- | ---: | ---: | ---: |
| CFBD enriched baseline | top 12 | 6/16 | 0.375 | 0.292 |
| scoring format fit plus | top 12 | 7/16 | 0.438 | 0.250 |
| CFBD enriched baseline | top 24 | 11/16 | 0.688 | 0.396 |
| scoring format fit plus | top 24 | 11/16 | 0.688 | 0.375 |
| CFBD enriched baseline | top 36 | 12/16 | 0.750 | 0.514 |
| scoring format fit plus | top 36 | 13/16 | 0.812 | 0.472 |

Decision: `scoring_format_fit_plus` is the best audit candidate because it improves validation Top 12 and Top 36 star capture while reducing selected bust rates. This is enough for an audit finding, not enough for a v2 board.

## WR result

Full WR position Top 24:

| Model | Stars | Star capture | Bust rate |
| --- | ---: | ---: | ---: |
| CFBD enriched baseline | 9/37 | 0.243 | 0.167 |
| scoring format fit plus | 10/37 | 0.270 | 0.167 |

WR verdict: YELLOW. The best candidate improves full-position WR Top 24 capture slightly, but Phase A showed validation WR Top 12 remains brittle. WR tuning still needs richer source-safe features such as route participation/YPRR, YAC/contact, contested catch, injury context, and warning visibility.

## V2 board decision

V2 candidate board created: no.

Reasons:

- this was an audit runway, not a board-promotion prompt;
- 127 complete-window rows still lack deterministic CFBD enriched features;
- 8 duplicate-selected rows remain manual-review rows;
- validation WR Top 12 remains fragile;
- warnings/manual-review context must stay visible before any current-year board is generated.

## Exports created

Local-only Phase B exports:

- `local_exports/rookie_framework/cfbd_enriched_tuning_candidate_v1_20260615/cfbd_enriched_candidate_configs_20260615.csv`
- `cfbd_enriched_candidate_metrics_by_split_20260615.csv`
- `cfbd_enriched_candidate_metrics_by_year_20260615.csv`
- `cfbd_enriched_candidate_metrics_by_position_20260615.csv`
- `cfbd_enriched_top_missed_stars_20260615.csv`
- `cfbd_enriched_high_ranked_busts_20260615.csv`
- `cfbd_enriched_candidate_decision_20260615.csv`
- `README_ROOKIE_CFBD_ENRICHED_TUNING_CANDIDATE_V1_20260615.md`

No `rookie_draft_ranking_v2_cfbd_candidate_20260615.csv` was created.

## Anti-cheat / leakage audit

| Check | Result |
| --- | --- |
| No player-specific tuning rules | PASS |
| No `if player == ...` boosts/penalties | PASS |
| Names appear only in diagnostics | PASS |
| IDs used only for identity/join/grouping | PASS |
| Schools, teams, and draft years not scoring features | PASS |
| Outcome labels used only for evaluation | PASS |
| 2024-2025 partial-window rows excluded | PASS |
| ADP/market/public rankings/projections/trade calculators excluded | PASS |
| No future stats used as features | PASS |
| No probabilities, bands, hidden sort keys, app wiring, production rankings, Outcome files, veteran files, or promoted artifacts touched | PASS |

## Recommended next step

Do not create a v2 board yet.

Recommended rookie-only next task: run a CFBD-enriched manual-review reduction pass focused on the 127 unresolved rows and 8 duplicate-selected rows, then rerun candidate validation with explicit warning visibility. If that remains GREEN, a separate prompt can decide whether to create a local-only experimental v2 current-year board.
