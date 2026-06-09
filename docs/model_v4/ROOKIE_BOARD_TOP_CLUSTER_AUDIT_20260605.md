# Rookie Board Top-Cluster Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: inspect the top rookie board cluster, evidence components, trust caps,
and warning groups before any formula work. This report is evidence only. It
does not change rookie weights, model weights, pick baselines, VORP,
replacement formulas, confidence caps, generated outputs, Draft Room state,
War Board state, or recommendation logic.

## Source

- Source path:
  `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- Primary score column: `league_format_adjusted_score`
- Raw prospect score column: `prospect_private_value_review_score`
- Lineage/surface: Rookie Draft Board review rows
- Allowed use: `review_only_rookie_board_context_not_final_pick`
- Blocked use: `do_not_use_as_final_rookie_draft_recommendation`
- Formula version: `model_v4_sprint_14e_rookie_draft_review_0.1.0`

This audit also references `docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md`
for named rookie audit anchors.

## Board Snapshot

- Total rookie board rows: 210.
- Evidence status counts:
  - `manual_scout_source_review`: 122.
  - `draftable_review`: 67.
  - `watchlist_data_incomplete`: 21.
- Draft board band counts:
  - `manual_scout_context_review`: 122.
  - `watchlist_context_review`: 22.
  - `watchlist_or_data_incomplete_context_review`: 21.
  - `second_round_board_context_review`: 19.
  - `depth_board_context_review`: 16.
  - `first_round_board_context_review`: 10.
- Rows with `league_format_adjusted_score` at least 50: 10.

## Top 20 Rookie Board Rows

| Rank | Prospect | Pos | College | NFL Team | Raw Score | Format Score | Confidence Cap | Component Weight | Evidence Status | Board Band | Roster Context | Warning Preview |
|---:|---|---|---|---|---:|---:|---:|---:|---|---|---|---|
| 1 | Jeremiyah Love | RB | Notre Dame | ARI | 75.3111 | 75.3111 | 0.82 | 1.0 | draftable_review | first_round_board_context_review | possible_rb_roster_fit_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; workout_metric_missing_after_zero_repair; ... |
| 2 | Makai Lemon | WR | USC | PHI | 69.2158 | 69.2158 | 0.88 | 1.0 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; source_limited_evidence_cap |
| 3 | Skyler Bell | WR | UConn | BUF | 64.0090 | 64.0090 | 0.82 | 1.0 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 4 | Jordyn Tyson | WR | Arizona State | NO | 70.8920 | 62.3850 | 0.82 | 0.88 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 5 | Chris Brazzell | WR | Tennessee | CAR | 57.7934 | 57.7934 | 0.82 | 1.0 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 6 | Ted Hurst | WR | Georgia State | TB | 60.0277 | 57.0263 | 0.82 | 0.95 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 7 | Carnell Tate | WR | Ohio State | TEN | 56.1780 | 56.1780 | 0.82 | 1.0 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 8 | Antonio Williams | WR | Clemson | WAS | 54.2258 | 54.2258 | 0.82 | 1.0 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 9 | Chris Bell | WR | Louisville | MIA | 60.0970 | 52.8854 | 0.82 | 0.88 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 10 | Malachi Fields | WR | Notre Dame | NYG | 51.2729 | 51.2729 | 0.82 | 1.0 | draftable_review | first_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 11 | Caleb Douglas | WR | Texas Tech | MIA | 49.3809 | 49.3809 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 12 | Ja'Kobi Lane | WR | USC | BAL | 49.2653 | 49.2653 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; workout_metric_missing_after_zero_repair; workout_metric_zero_placeholder_repaired; ... |
| 13 | Omar Cooper | WR | Indiana | NYJ | 48.0827 | 48.0827 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; workout_metric_missing_after_zero_repair; ... |
| 14 | Lewis Bond | WR | Boston College | HOU | 52.1173 | 47.9479 | 0.94 | 0.92 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; combine_absent_not_zero_filled; missing_age_lifecycle_component; draft_capital_anchor_warning |
| 15 | Denzel Boston | WR | Washington | CLE | 47.9183 | 47.9183 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 16 | Emmett Johnson | RB | Nebraska | KC | 47.5600 | 47.5600 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | possible_rb_roster_fit_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 17 | Zachariah Branch | WR | Georgia | ATL | 46.2541 | 46.2541 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 18 | KC Concepcion | WR | Texas A&M | CLE | 52.1030 | 45.8506 | 0.82 | 0.88 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 19 | Germie Bernard | WR | Alabama | PIT | 45.7444 | 45.7444 | 0.82 | 1.0 | draftable_review | second_round_board_context_review | wr_room_crowded_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; source_limited_evidence_cap |
| 20 | Nicholas Singleton | RB | Penn State | TEN | 51.0400 | 44.9152 | 0.88 | 0.88 | draftable_review | second_round_board_context_review | possible_rb_roster_fit_context | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; source_limited_evidence_cap; missing_athletic_prior_component; ... |

## Top-20 Warning Group Counts

- `market_context_excluded_from_private_value`: 20 of 20.
- `source_limited_evidence_cap`: 19 of 20.
- `third_party_combine_source_limited`: 19 of 20.
- `current_college_team_mismatch_quarantined`: 16 of 20.
- `missing_athletic_prior_component`: 4 of 20.
- Workout metric repair warnings: 3 of 20.
- `model_edge_weirdness`: 1 of 20.
- `manual_scout_source_review`: 0 of 20.

## Named Rookie Audit Anchors

| Audit ID | Prospect | Board Rank | Position | Format Score | Evidence Status | Notes |
|---|---|---:|---|---:|---|---|
| A69 | Jeremiyah Love | 1 | RB | 75.3111 | draftable_review | Top rookie board anchor; current-college and source-limited warnings present. |
| A70 | Makai Lemon | 2 | WR | 69.2158 | draftable_review | Top WR rookie anchor; source-limited warnings present. |
| A71 | Skyler Bell | 3 | WR | 64.0090 | draftable_review | Top cluster row with `model_edge_weirdness` warning. |
| A72 | Jordyn Tyson | 4 | WR | 62.3850 | draftable_review | Format score below raw score due component availability/adjustment context. |
| A73 | Carnell Tate | 7 | WR | 56.1780 | draftable_review | Rookie/current bridge audit anchor. |
| A74 | Antonio Williams | 8 | WR | 54.2258 | draftable_review | Pick-window candidate in first-round board context. |
| A75 | Daniel Sobkowicz | 85 | WR | 25.2000 | watchlist_data_incomplete | Not top cluster; reserved for low-evidence/watchlist audit. |

## Review Observations

- The top 10 rookie board rows are all `first_round_board_context_review`.
- The top 20 rookie board rows are all `draftable_review`.
- The top cluster is WR-heavy: only `Jeremiyah Love`, `Emmett Johnson`, and
  `Nicholas Singleton` are RBs in the top 20.
- Every top-20 row explicitly excludes market context from private value.
- Most top-20 rows carry source-limited and third-party-combine warnings; this is
  a human scouting prompt, not a formula verdict.
- `Daniel Sobkowicz` is intentionally not treated as a top-cluster row. He is
  included here only to route him to R13, the low-evidence/watchlist audit.

## Non-Goals

- Do not change rookie weights from this report.
- Do not change model weights, pick baselines, VORP, replacement formulas,
  confidence caps, age curves, or startup-slot conversion.
- Do not mutate generated rookie outputs, Draft Room state, War Board state, or
  user-entered draft state.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert any review label into a trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendation.
