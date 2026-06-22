# NWR Overnight Cross-Asset + Outcome App Repair - 2026-06-22

Final verdict: YELLOW-GREEN. The app-facing layer is morning-usable as review-only context.

## What Changed

- Built `emergency_cross_asset_candidate_player_board.csv` from approved/internal NWR sources.
- Rookie raw scores are no longer compared directly to dropped-veteran candidate values.
- Draft-room `cross_asset_candidate_rank` is now ranked within the frozen 66-player draft pool.
- Full-board context keeps `emergency_overall_context_rank` for diagnostics.
- Startup ADP remains display-only and is transformed into available-pool ADP rank/range.
- Created candidate/review-only 2026, 2027, and Next-5Y horizon bands. No horizon probabilities were fabricated.
- Player Compare includes candidate-vs-frozen notes and a Horizon Outcome Candidate block.

## Formula

`emergency_cross_asset_value = internal value anchor + age curve + 10-team 1QB position scarcity + role evidence + small applicable Outcome support - uncertainty penalty`

ADP is not used in the value formula. Outcome is display-only and only a small support/confidence signal when applicable.

## Top Draft-Pool Candidate View
| emergency_cross_asset_rank | player | pos | final_board_rank | dynasty_rank | emergency_cross_asset_value | confidence_band | available_pool_adp_range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Jeremiyah Love | RB | 1 | Not enough information | 61.70 | Medium | Late 1st equivalent |
| 2 | Zay Flowers | WR | 31 | 12 | 57.03 | Medium-high | Depth / later |
| 3 | Chris Olave | WR | 34 | 14 | 54.57 | Medium-high | Depth / later |
| 4 | Makai Lemon | WR | 2 | Not enough information | 49.20 | Low | Depth / later |
| 5 | Jameson Williams | WR | 42 | 26 | 48.99 | Medium-high | Depth / later |
| 6 | Alec Pierce | WR | 47 | 27 | 48.45 | Medium-high | Depth / later |
| 7 | Carnell Tate | WR | 3 | Not enough information | 48.40 | Low | Depth / later |
| 8 | KC Concepcion | WR | 4 | Not enough information | 46.70 | Low | Depth / later |
| 9 | Jadarian Price | RB | 5 | Not enough information | 45.70 | Low | Depth / later |
| 10 | Denzel Boston | WR | 6 | Not enough information | 42.70 | Low | Depth / later |
| 11 | Drake Maye | QB | 40 | 23 | 38.35 | Low | Late 1st equivalent |
| 12 | Germie Bernard | WR | 7 | Not enough information | 38.20 | Low | Depth / later |
| 13 | Chris Bell | WR | 8 | Not enough information | 36.40 | Low | Depth / later |
| 14 | Zachariah Branch | WR | 9 | Not enough information | 35.60 | Low | Depth / later |
| 15 | Jonah Coleman | RB | 11 | Not enough information | 35.00 | Low | Depth / later |

## Named Sanity Anchors
| emergency_cross_asset_rank | player | pos | final_board_rank | dynasty_rank | emergency_cross_asset_value | confidence_band |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Jeremiyah Love | RB | 1 | Not enough information | 61.70 | Medium |
| 2 | Zay Flowers | WR | 31 | 12 | 57.03 | Medium-high |
| 3 | Chris Olave | WR | 34 | 14 | 54.57 | Medium-high |
| 4 | Makai Lemon | WR | 2 | Not enough information | 49.20 | Low |
| 5 | Jameson Williams | WR | 42 | 26 | 48.99 | Medium-high |
| 7 | Carnell Tate | WR | 3 | Not enough information | 48.40 | Low |
| 8 | KC Concepcion | WR | 4 | Not enough information | 46.70 | Low |
| 9 | Jadarian Price | RB | 5 | Not enough information | 45.70 | Low |
| 11 | Drake Maye | QB | 40 | 23 | 38.35 | Low |
| 19 | Jaylen Warren | RB | 54 | 43 | 28.20 | Medium |
| 20 | Rashee Rice | WR | 62 | 79 | 26.27 | Medium |
| 22 | Brian Thomas | WR | 63 | 82 | 23.69 | Medium |
| 57 | Dak Prescott | QB | 60 | 70 | 10.06 | Low |
| 63 | Brock Purdy | QB | 65 | 185 | 3.34 | Medium |
| 65 | Keenan Allen | WR | 64 | 124 | 0.94 | Low |
| 66 | Darren Waller | TE | 66 | 226 | 0.00 | Low |

## Outcome

- Current approved Outcome columns remain: QB T12, RB T12, RB T24, WR T12, WR T24, WR T36, TE T12.
- Horizon candidate rows: 1902. These are categorical bands only.
- Same-position unsupported Outcome stays `Not enough information`; wrong-position Outcome is hidden by default / N/A in advanced views.

## Guardrails

No latest_candidate/latest_approved update, no pinned snapshot mutation, no frozen-board mutation, no Final Board Rank change, no Dynasty Rank overwrite, no raw vendor CSVs, and no raw prediction dumps.

Detailed phase logs are under `docs/hq/parallel_lanes/overnight_8h_emergency_20260622/` and `docs/hq/parallel_lanes/overnight_emergency_logs_20260622/`.

## Validation Summary

- Compile/import checks: PASS.
- CSV load validation: PASS for emergency candidate board and horizon candidate bands.
- Service load validation: PASS, frozen board 66 rows and Dynasty Rankings 240 rows.
- Browser smoke: PASS for Live Draft Room, Dynasty Rankings, Player Compare, Mock Draft, Trading Lab, Settings / Data Health, and Outcome Diagnostics.
- Live Draft interaction proof: Assign 1.01 advanced to 1.02 and changed counts to Drafted 1 / Available 65; Undo restored Drafted 0 / Available 66 and current pick 1.01.
- Focused pytest/Ruff: YELLOW environment gap. Local `.venv` did not have pytest or ruff installed, and no global pytest/ruff command was available.
