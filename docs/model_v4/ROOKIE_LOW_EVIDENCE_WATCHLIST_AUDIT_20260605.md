# Rookie Low-Evidence Watchlist Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: inspect watchlist and data-incomplete rookie rows and verify they do
not masquerade as confident draft options. This report is evidence only. It
does not change rookie weights, model weights, pick baselines, VORP,
replacement formulas, confidence caps, generated outputs, Draft Room state,
War Board state, user-entered draft state, or recommendation logic.

## Source

- Source path:
  `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- Primary score column: `league_format_adjusted_score`
- Raw prospect score column: `prospect_private_value_review_score`
- Lineage/surface: Rookie Draft Board review rows
- Allowed use: `review_only_rookie_board_context_not_final_pick`
- Blocked use: `do_not_use_as_final_rookie_draft_recommendation`
- Formula version: `model_v4_sprint_14e_rookie_draft_review_0.1.0`

This audit follows `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`, which routed
`Daniel Sobkowicz` here instead of treating him as a top-cluster rookie.

## Watchlist Snapshot

- Total rookie board rows: 210.
- Watchlist/data-incomplete union rows reviewed: 43.
- Evidence status inside the union:
  - `draftable_review`: 22.
  - `watchlist_data_incomplete`: 21.
- Draft board bands inside the union:
  - `watchlist_context_review`: 22.
  - `watchlist_or_data_incomplete_context_review`: 21.
- Score bands inside the union:
  - 50 or above: 0.
  - 40 to 49.999: 0.
  - 30 to 39.999: 1.
  - 20 to 29.999: 21.
  - below 20: 21.
- Every reviewed row carries:
  - `review_only_no_final_rookie_pick_recommendation`.
  - `market_context_excluded_from_private_value`.
  - `do_not_use_as_final_rookie_draft_recommendation`.

## Watchlist/Data-Incomplete Rows

| Rank | Prospect | Pos | College | NFL Team | Format Score | Confidence Cap | Evidence Status | Board Band | Warning Preview |
|---:|---|---|---|---|---:|---:|---|---|---|
| 61 | Seydou Traore | TE | Mississippi State | MIA | 30.6507 | 0.88 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 63 | Deion Burks | WR | Oklahoma | IND | 29.5997 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 70 | Oscar Delp | TE | Georgia | NO | 27.2536 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 72 | Athan Kaliakmanis | QB | Rutgers | WAS | 27.1282 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 75 | Cade Klubnik | QB | Clemson | NYJ | 26.5652 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; workout_metric_missing_after_zero_repair; ... |
| 80 | Ty Simpson | QB | Alabama | LAR | 25.9487 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; workout_metric_missing_after_zero_repair; ... |
| 81 | Bauer Sharp | TE | LSU | TB | 25.8964 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 84 | Drew Allar | QB | Penn State | PIT | 25.3158 | 0.88 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 85 | Daniel Sobkowicz | WR | Illinois State | blank | 25.2000 | 0.84 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; missing_prospect_or_college_evidence; combine_absent_not_zero_filled; ... |
| 89 | Barion Brown | WR | LSU | NO | 24.5849 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 93 | Colbie Young | WR | Georgia | CIN | 24.1758 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 95 | Nate Boerkircher | TE | Texas A&M | JAX | 23.8216 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 96 | Jack Endries | TE | Texas | CIN | 23.8094 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 98 | Taylen Green | QB | Arkansas | CLE | 23.5898 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 106 | Jaren Kanak | TE | Oklahoma | TEN | 22.4908 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 107 | Will Kacmarek | TE | Ohio State | MIA | 22.1057 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 109 | Garrett Nussmeier | QB | LSU | KC | 21.7060 | 0.88 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 112 | Dallen Bentley | TE | Utah | DEN | 21.3714 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 114 | Richard Reese | RB | Stephen F. Austin | blank | 20.8947 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 116 | Matthew Hibner | TE | SMU | BAL | 20.7774 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 118 | Carsen Ryan | TE | BYU | CLE | 20.7219 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 119 | Malik Benson | WR | Oregon | LV | 20.7010 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 127 | Josh Cuevas | TE | Alabama | BAL | 19.6492 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 130 | Kaden Wetjen | WR | Iowa | PIT | 19.4732 | 0.88 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; source_limited_evidence_cap; ... |
| 140 | Barika Kpeenu | RB | North Dakota State | blank | 17.6193 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 141 | Michael Wortham | WR | Montana | blank | 17.5639 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 151 | Jalen Walthall | WR | Incarnate Word | blank | 16.0179 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 153 | Savion Red | RB | Sacramento State | blank | 15.9200 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 154 | Reggie Virgil | WR | Texas Tech | ARI | 15.7728 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 157 | Behren Morton | QB | Texas Tech | NE | 15.3140 | 0.82 | draftable_review | watchlist_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; third_party_combine_source_limited; workout_metric_missing_after_zero_repair; ... |
| 163 | DJ Rogers | TE | TCU | DAL | 14.4954 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; missing_college_market_share; third_party_combine_source_limited; ... |
| 177 | Riley Nowakowski | TE | Indiana | PIT | 11.7531 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; third_party_combine_source_limited; ... |
| 179 | Jaydn Ott | RB | Oklahoma | KC | 11.3276 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 188 | Cade McNamara | QB | East Tennessee State | blank | 10.3828 | 0.84 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_prospect_or_college_evidence; ... |
| 189 | Dae'Quan Wright | TE | Mississippi | PHI | 10.3001 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 190 | Carson Beck | QB | Miami (FL) | ARI | 9.7308 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 196 | Armoni Goodwin | RB | UT Martin | blank | 8.5577 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 197 | CJ Daniels | WR | Miami (FL) | LAR | 8.0718 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 201 | Harrison Wallace III | WR | Mississippi | ARI | 6.2470 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 204 | Jam Miller | RB | Alabama | NE | 5.4278 | 0.80 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; admitted_without_big_board_identity_receipt; missing_college_market_share; ... |
| 205 | Chip Trayanum | RB | Toledo | blank | 5.3333 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |
| 208 | Ty Thompson | TE | Tulane | blank | 3.3433 | 0.88 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; combine_absent_not_zero_filled; ... |
| 209 | Logan Diggs | RB | Mississippi | blank | 3.2679 | 0.82 | watchlist_data_incomplete | watchlist_or_data_incomplete_context_review | review_only_no_final_rookie_pick_recommendation; market_context_excluded_from_private_value; current_college_team_mismatch_quarantined; missing_college_market_share; ... |

## Explicit Data-Incomplete Rows

These 21 rows carry `watchlist_data_incomplete`. They should be handled as
manual scouting prompts, not confident draft options.

| Rank | Prospect | Pos | Format Score | Confidence Cap | Primary Data Gap Signal |
|---:|---|---|---:|---:|---|
| 85 | Daniel Sobkowicz | WR | 25.2000 | 0.84 | missing_prospect_or_college_evidence |
| 112 | Dallen Bentley | TE | 21.3714 | 0.88 | third_party_combine_source_limited |
| 114 | Richard Reese | RB | 20.8947 | 0.88 | current_college_team_mismatch_quarantined |
| 140 | Barika Kpeenu | RB | 17.6193 | 0.88 | current_college_team_mismatch_quarantined |
| 141 | Michael Wortham | WR | 17.5639 | 0.88 | current_college_team_mismatch_quarantined |
| 151 | Jalen Walthall | WR | 16.0179 | 0.82 | current_college_team_mismatch_quarantined |
| 153 | Savion Red | RB | 15.9200 | 0.88 | current_college_team_mismatch_quarantined |
| 154 | Reggie Virgil | WR | 15.7728 | 0.82 | current_college_team_mismatch_quarantined |
| 163 | DJ Rogers | TE | 14.4954 | 0.82 | missing_college_market_share |
| 177 | Riley Nowakowski | TE | 11.7531 | 0.82 | current_college_team_mismatch_quarantined |
| 179 | Jaydn Ott | RB | 11.3276 | 0.82 | current_college_team_mismatch_quarantined |
| 188 | Cade McNamara | QB | 10.3828 | 0.84 | current_college_team_mismatch_quarantined |
| 189 | Dae'Quan Wright | TE | 10.3001 | 0.82 | current_college_team_mismatch_quarantined |
| 190 | Carson Beck | QB | 9.7308 | 0.82 | current_college_team_mismatch_quarantined |
| 196 | Armoni Goodwin | RB | 8.5577 | 0.88 | current_college_team_mismatch_quarantined |
| 197 | CJ Daniels | WR | 8.0718 | 0.82 | current_college_team_mismatch_quarantined |
| 201 | Harrison Wallace III | WR | 6.2470 | 0.82 | current_college_team_mismatch_quarantined |
| 204 | Jam Miller | RB | 5.4278 | 0.80 | admitted_without_big_board_identity_receipt |
| 205 | Chip Trayanum | RB | 5.3333 | 0.82 | current_college_team_mismatch_quarantined |
| 208 | Ty Thompson | TE | 3.3433 | 0.88 | current_college_team_mismatch_quarantined |
| 209 | Logan Diggs | RB | 3.2679 | 0.82 | current_college_team_mismatch_quarantined |

## Warning Coverage

- `review_only_no_final_rookie_pick_recommendation`: 43 of 43.
- `market_context_excluded_from_private_value`: 43 of 43.
- `missing_age_lifecycle_component`: 41 of 43.
- `current_college_team_mismatch_quarantined`: 33 of 43.
- `third_party_combine_source_limited`: 32 of 43.
- `source_limited_evidence_cap`: 32 of 43.
- `source_shape_warning`: 23 of 43.
- `missing_recruiting_prior_component`: 22 of 43.
- `watchlist_or_data_incomplete_context_review`: 21 of 43.
- `missing_market_share_component`: 19 of 43.
- `missing_prospect_or_college_evidence`: 13 of 43.

## Review Observations

- No watchlist/data-incomplete row has a `league_format_adjusted_score` at or
  above 50, so none sits in the current first-round/top-cluster score band.
- The highest reviewed row is `Seydou Traore` at 30.6507, which is still a
  watchlist-context score and carries final-pick blocked use.
- `Daniel Sobkowicz` is the highest explicit `watchlist_data_incomplete` row at
  rank 85 and score 25.2000. His blank NFL team plus
  `missing_prospect_or_college_evidence` warning make him a named manual-scout prompt, not a confident draft option.
- The 22 `draftable_review` rows in `watchlist_context_review` are not the same
  as the 21 explicit data-incomplete rows, but both groups are review-only and
  blocked from final rookie pick use.
- Market context is present only as an exclusion warning. It is not a private
  value input and does not promote any watchlist row into a confident pick lane.

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
