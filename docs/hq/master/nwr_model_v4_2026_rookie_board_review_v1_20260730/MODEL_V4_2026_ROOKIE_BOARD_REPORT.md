# Model V4 2026 Rookie Board Report

Verdict: `YELLOW_NWR_MODEL_V4_2026_ROOKIE_BOARD_BUILT_WITH_SOURCE_LIMITS`.

The actual `model_v4_sprint_12_13_review_0.1.1` and
`model_v4_sprint_14e_rookie_draft_review_0.1.0` public builders executed against
the governed 2026 drafted class. The result is a separate **Review-Only** board,
not a production Dynasty Rank, recommendation, Finished V1 update, Outcome V3
input, or Trading Lab input.

## Mechanical coverage

- Drafted QB/RB/WR/TE rows: 80
- Exact GSIS identities and scored rows: 73
- Blocked unresolved identities and unscored rows: 7
- Exact by position: QB 9, RB 11, WR 33, TE 20
- Blocked by position: QB 1, RB 1, WR 3, TE 2
- Component coverage: `{"age_component": 73, "athletic_component": 16, "draft_capital_component": 73, "market_share_component": 73, "production_component": 73, "recruiting_component": 0}`
- Recruiting coverage: 0/73; missing is never zero
- Raw combine-source missingness: 20/73
- Athletic score coverage under the pre-existing workout consumer: 16/73
- Confidence caps: `{"0.84": 20, "0.88": 53}`
- Two-root governed digest: `cd5ff629dcf159950e3f23dc75bbb713c225dd4c7e7bffe2a5496e209a231f70`
- Required negative controls: 20/20 rejected

Raw nflverse combine measurements were preserved in `workout_profile`. No
governed percentile-regeneration algorithm exists in the current code, so raw
measurements were not converted into invented percentiles. The existing TE
consumer can still use admitted weight; other unavailable percentile-dependent
athletic scores remain missing.

## Top review board

| Rank | Player | Pos | Sprint 14E format score | Tier |
| ---: | --- | --- | ---: | --- |
| 1 | Jeremiyah Love | RB | 67.3430 | first_round_board_context_review |
| 2 | Jordyn Tyson | WR | 63.6383 | first_round_board_context_review |
| 3 | Makai Lemon | WR | 61.0297 | first_round_board_context_review |
| 4 | Jonah Coleman | RB | 56.8169 | first_round_board_context_review |
| 5 | Skyler Bell | WR | 56.3409 | first_round_board_context_review |
| 6 | Denzel Boston | WR | 54.9684 | first_round_board_context_review |
| 7 | Emmett Johnson | RB | 54.3263 | first_round_board_context_review |
| 8 | Carnell Tate | WR | 53.8710 | first_round_board_context_review |
| 9 | Chris Bell | WR | 53.7450 | first_round_board_context_review |
| 10 | Omar Cooper Jr. | WR | 53.5544 | first_round_board_context_review |
| 11 | Zachariah Branch | WR | 50.6410 | second_round_board_context_review |
| 12 | Germie Bernard | WR | 50.2426 | second_round_board_context_review |
| 13 | Ted Hurst | WR | 50.0000 | watchlist_or_data_incomplete_context_review |
| 14 | KC Concepcion | WR | 50.0000 | watchlist_or_data_incomplete_context_review |
| 15 | Malachi Fields | WR | 48.7492 | second_round_board_context_review |

## Position leaders

| Pos | Player | Overall review rank | Format score |
| --- | --- | ---: | ---: |
| QB | Fernando Mendoza | 30 | 41.8707 |
| RB | Jeremiyah Love | 1 | 67.3430 |
| TE | Kenyon Sadiq | 20 | 42.5022 |
| WR | Jordyn Tyson | 2 | 63.6383 |

## Historical review cluster

The current deterministic order is not preserved from historical assumptions.
It follows the reconstructed 2026 inputs, confidence caps, component availability,
position factors, guardrails, and Sprint 14E evidence adjustment.

| Player | Current review rank | Final analyzer score | Format score |
| --- | ---: | ---: | ---: |
| Jeremiyah Love | 1 | 81.1362 | 67.3430 |
| Jordyn Tyson | 2 | 76.6727 | 63.6383 |
| Makai Lemon | 3 | 73.5297 | 61.0297 |
| Skyler Bell | 5 | 67.8806 | 56.3409 |

## Interpretation limits

`DRAFT_CAPITAL_DISAGREEMENTS.csv` mechanically identifies risers and fallers.
`TOP_FLOOR_UPSIDE_RISK_PROFILES.csv` defines floor, upside, and risk as reporting
lenses, not new scoring components. CFBD PPA and usage are excluded. CFBD counting
stats and exact team denominators reconstruct only existing production/share
definitions. No formula weight changed.
