# Kaggle NFL Draft 2026 Dataset Validation - 2026-05-17

Raw zip preserved at: `C:\Dev\niners-war-room\local_exports\model_v4\raw_user_exports\rookie_manual\incoming\kaggle_nfl_draft_2026\nfl-draft-2026.zip`
Extracted raw CSV folder: `C:\Dev\niners-war-room\local_exports\model_v4\raw_user_exports\rookie_manual\incoming\kaggle_nfl_draft_2026\extracted`

## Verdict

This dataset is useful for the Model v4 rookie/prospect blocker. It should feed identity normalization, draft-capital backtesting, and prospect-context priors. It should not directly set private dynasty value, and mock/consensus/ADP style data must remain context or prior evidence with confidence caps.

## File Classification

| File | Rows | Columns | Model Lane | Recommended Use |
|---|---:|---:|---|---|
| `big_board_picks.csv` | 102171 | 10 | noisy_prospect_context | large public big-board pick history; useful for aggregate consensus only |
| `big_boards.csv` | 1368 | 7 | source_metadata | metadata for big_board_picks |
| `consensus_big_board.csv` | 6254 | 6 | historical_backtest_context | historical consensus board for draft-capital expectation/backtesting |
| `consensus_big_board_latest_2026.csv` | 731 | 6 | prospect_context | 2026 consensus board for rookie prior/context after position-map validation |
| `draft_order.csv` | 2568 | 4 | draft_context | draft order context; not fantasy private value |
| `draft_results.csv` | 2564 | 8 | historical_backtest_and_draft_capital | 2016-2025 actual draft capital for backtesting prospect priors |
| `first_round_mocks.csv` | 9936 | 7 | mock_draft_context | metadata for first-round mocks; team-need context only |
| `first_round_picks.csv` | 311672 | 10 | mock_draft_context | large first-round mock pick history; not private value |
| `player_position_2026_mapping.csv` | 713 | 2 | identity_position_context | 2026 official player-position mapping for prospect identity normalization |
| `players_nflverse.csv` | 24376 | 39 | identity_crosswalk | nflverse player identity metadata |
| `sample_submission.csv` | 257 | 714 | competition_artifact | not needed for fantasy model |
| `solution.csv` | 257 | 4 | competition_artifact | competition public/private split; not fantasy model value |
| `team_mocks.csv` | 8811 | 7 | mock_draft_context | metadata for team mocks; team-need context only |
| `team_picks.csv` | 61274 | 10 | mock_draft_context | team mock picks; team-need context only |

## Quality Notes

- `consensus_big_board_latest_2026.csv` has `731` players.
- `player_position_2026_mapping.csv` has `713` players.
- `18` latest-board players are missing from the official 2026 position mapping and must be flagged in the crosswalk.
- Missing position-map examples: Anterio Thompson (DL, Washington); Bryce Phillips (CB, San Diego State); Cameron Dorner (WR, North Texas); Daniel Sobkowicz (WR, Illinois State); DT Sheffield (WR, Rutgers); Erick Hunter (LB, Morgan State); Gavin Ortega (OT, Weber State); Gunner Maldonado (S, Kansas State); Henry Lutovsky (IOL, Nebraska); Jack Dingle (LB, Cincinnati); Jack Strand (QB, Minnesota State-Moorhead); Javin Wright (LB, Nebraska); Khalil Jacobs (LB, Missouri); Rodney Shelley (CB, Georgia Tech); Sieh Bangura (RB, Ohio); Tamarion Crumpley (CB, UAB); Tanner Wall (S, BYU); Wesley Bailey (EDGE, Louisville)
- Historical `draft_results.csv` has `1` duplicate draft-year/player-name keys.
- Duplicate example: 2019 David Long x2
- `players_nflverse.csv` is useful as identity metadata but should not be assumed to cover all 2026 prospects.
- `sample_submission.csv` and `solution.csv` are competition artifacts, not model evidence.

## Integration Rules

- Use actual draft results/draft capital as stronger evidence than mock or consensus data when available.
- Use 2026 consensus board and mock data as prospect context / expected-draft-capital prior only, with receipts and confidence caps.
- Keep rookie ADP, fantasy rankings, and mock popularity out of private football value unless explicitly modeled as context-only or prior evidence.
- Build a prospect identity crosswalk keyed by normalized name, draft year, player URL, college, position, and source-specific IDs where available.
- Flag all ambiguous joins, including duplicate historical names such as 2019 David Long.
- Re-run rookie/prospect audits after this is integrated with CFBD/RotoWire/FantasyPros rookie data.