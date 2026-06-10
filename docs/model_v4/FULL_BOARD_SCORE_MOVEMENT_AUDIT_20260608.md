# Full Board Score Movement Audit - 2026-06-08

## Verdict

**full_board_rankings_ready_for_human_review**

This audit is evidence-only. No formula weights, replacement defaults, VORP formulas, confidence cap magnitudes, market thresholds, startup conversion, active rankings, or Decision Board logic were changed by this audit.

## Direct Answers

- Scores did not change only because ranks now compare against 232 players. Rank movement is partly universe expansion, but numeric NWR scores also changed for some players.
- Numeric score movement is expected from the existing design because the full-board run recomputed replacement/VORP baselines and position max normalizers over the active QB/RB/WR/TE universe.
- The formula design is universe-sensitive by construction: replacement players are chosen from the admitted player pool, positive VORP is computed against that replacement row, and VORP/first-down components are normalized by position maxima.
- Large movements are flagged below for human review. The audit found no market, league, ADP, projection, trade-calculator, or legacy private-score contamination.
- The full-board export should remain human-review baseline, not promoted as final roster or trade guidance.

## Coverage Summary

| Metric | Count |
| --- | ---: |
| active_rows | 240 |
| qb_rb_wr_te_rows | 232 |
| k_rows | 8 |
| nwr_scored_rows | 232 |
| no_private_score_rows | 8 |
| source_repair_needed_rows | 8 |
| old_new_matched_rows | 71 |
| stable_rows | 3 |
| large_score_movers | 19 |
| large_rank_movers | 28 |
| my_team_rows | 24 |
| available_rows | 0 |
| rookie_rows | 0 |

## Universe-Sensitive Components

| Component | Universe-sensitive? | Evidence |
| --- | --- | --- |
| Replacement baselines | Yes | Replacement player is selected from position rows in the admitted pool. |
| VORP anchors | Yes | VORP is scored against the selected replacement player. |
| Percentile/scaling calculations | Yes | VORP and first-down component scores use position max ceilings. |
| Position medians/means | No direct checkpoint median/mean dependency found | Current-value services use max ceilings and averages of present components, not population medians. |
| Confidence caps | Potentially | Caps are per-player, but warning inputs can differ when the evidence universe is rebuilt. |
| Lifecycle distributions | Mostly no | Lifecycle modifier is per-player role/age evidence, not a distribution rank. |
| Warning gates | Potentially | Rebuilt evidence rows can change warning flags. |
| Rank assignment | Yes | New rank is assigned over 232 scored QB/RB/WR/TE rows. |

## Position Distribution Summary

### Old Checkpoint

| Pos | Count | Min | Max | Mean | Median |
| --- | ---: | ---: | ---: | ---: | ---: |
| QB | 8 | 8.99 | 80.31 | 40.12 | 35.83 |
| RB | 17 | 3.07 | 82.83 | 56.28 | 60.82 |
| WR | 36 | 16.21 | 83.05 | 42.58 | 37.3 |
| TE | 10 | 13.78 | 87.48 | 37.62 | 28.18 |

### Full Board

| Pos | Count | Min | Max | Mean | Median |
| --- | ---: | ---: | ---: | ---: | ---: |
| QB | 28 | 8.66 | 50.32 | 20.74 | 15.1 |
| RB | 79 | 3.07 | 78.46 | 20.54 | 12.8 |
| WR | 93 | 9.44 | 83.05 | 29.26 | 23.99 |
| TE | 32 | 4.09 | 62.26 | 18.49 | 14.39 |

### Full Board Score Bands

| Band | Count |
| --- | ---: |
| 80+ | 2 |
| 70-79.99 | 4 |
| 60-69.99 | 4 |
| 50-59.99 | 12 |
| 40-49.99 | 12 |
| 30-39.99 | 24 |
| 20-29.99 | 50 |
| under 20 | 124 |

### Position Balance Flags

- Top 25 position count: QB=2, RB=8, WR=13, TE=2.
- Top 50 position count: QB=5, RB=16, WR=26, TE=3.
- Bottom 25 position count: QB=2, RB=21, WR=0, TE=2.
- No automatic position-balance blocker triggered; human football review still required.

## Top 50 Full Board Players

| Rank | Player | Pos | Age | Team | Score | League | Market | Trust | Warnings |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| 1 | Puka Nacua | WR |  | LAR | 83.05 | 2 | 3.7 | Capped Score | 4 |
| 2 | Jaxon Smith-Njigba | WR |  | SEA | 82.57 | 5 | 7.7 | Capped Score | 4 |
| 3 | Bijan Robinson | RB |  | ATL | 78.46 | 1 | 2.7 | Capped Score | 4 |
| 4 | Jonathan Taylor | RB |  | IND | 74.31 | 7 | 16.5 | Capped Score | 6 |
| 5 | Jahmyr Gibbs | RB |  | DET | 70.73 | 3 | 4.0 | Capped Score | 4 |
| 6 | Ja'Marr Chase | WR |  | CIN | 70.54 | 4 | 1.7 | Capped Score | 4 |
| 7 | Amon-Ra St. Brown | WR |  | DET | 65.93 | 8 | 5.4 | Capped Score | 6 |
| 8 | Trey McBride | TE |  | ARI | 62.26 | 17 | 14.9 | Capped Score | 5 |
| 9 | De'Von Achane | RB |  | MIA | 61.33 | 10 | 20.4 | Capped Score | 4 |
| 10 | George Pickens | WR |  | DAL | 60.03 | 18 | 22.9 | Capped Score | 5 |
| 11 | James Cook | RB |  | BUF | 59.66 | 13 | 19.2 | Capped Score | 4 |
| 12 | Zay Flowers | WR |  | BAL | 56.53 | 43 | 51.0 | Capped Score | 4 |
| 13 | A.J. Brown | WR |  | PHI | 54.18 | 29 | 41.5 | Capped Score | 4 |
| 14 | Chris Olave | WR |  | NO | 54.07 | 25 | 29.9 | Capped Score | 5 |
| 15 | Kyren Williams | RB |  | LAR | 53.98 | 40 | 41.8 | Capped Score | 6 |
| 16 | Nico Collins | WR |  | HOU | 53.41 | 15 | 23.8 | Capped Score | 4 |
| 17 | Kyle Pitts | TE |  | ATL | 53.34 | 92 | 70.8 | Capped Score | 5 |
| 18 | Christian McCaffrey | RB |  | SF | 53.01 | 6 | 25.5 | Capped Score | 7 |
| 19 | Drake London | WR |  | ATL | 52.49 | 11 | 17.8 | Capped Score | 4 |
| 20 | CeeDee Lamb | WR |  | DAL | 51.1 | 9 | 13.7 | Capped Score | 5 |
| 21 | Josh Allen | QB |  | BUF | 50.32 | 24 | 8.0 | Capped Score | 3 |
| 22 | Justin Jefferson | WR |  | MIN | 50.25 | 19 | 11.8 | Capped Score | 5 |
| 23 | Drake Maye | QB |  | NE | 49.35 | 27 | 15.8 | Scored + Warnings | 2 |
| 24 | Chase Brown | RB |  | CIN | 49.19 | 35 | 35.3 | Capped Score | 4 |
| 25 | DeVonta Smith | WR |  | PHI | 48.62 | 61 | 65.8 | Capped Score | 4 |
| 26 | Jameson Williams | WR |  | DET | 48.49 | 37 | 63.2 | Capped Score | 5 |
| 27 | Alec Pierce | WR |  | IND | 47.95 | 82 | 76.1 | Capped Score | 4 |
| 28 | Trevor Lawrence | QB |  | JAX | 47.44 | 84 | 91.9 | Scored + Warnings | 1 |
| 29 | Courtland Sutton | WR |  | DEN | 42.94 | 55 | 109.0 | Capped Score | 5 |
| 30 | Tetairoa McMillan | WR |  | CAR | 42.83 | 30 | 21.2 | Capped Score | 4 |
| 31 | Breece Hall | RB |  | NYJ | 41.92 | 32 | 43.3 | Capped Score | 5 |
| 32 | Josh Jacobs | RB |  | GB | 41.24 | 26 | 47.2 | Capped Score | 7 |
| 33 | Jaylen Waddle | WR |  | DEN | 41.17 | 44 | 67.2 | Capped Score | 5 |
| 34 | Michael Wilson | WR |  | ARI | 40.19 | 86 | 77.0 | Capped Score | 4 |
| 35 | Tee Higgins | WR |  | CIN | 39.01 | 28 | 55.9 | Capped Score | 4 |
| 36 | DK Metcalf | WR |  | PIT | 38.9 | 60 | 89.1 | Capped Score | 6 |
| 37 | Javonte Williams | RB |  | DAL | 38.87 | 52 | 56.9 | Capped Score | 7 |
| 38 | Saquon Barkley | RB |  | PHI | 38.08 | 23 | 34.1 | Capped Score | 7 |
| 39 | D'Andre Swift | RB |  | CHI | 37.61 | 62 | 75.0 | Capped Score | 8 |
| 40 | Wan'Dale Robinson | WR |  | TEN | 36.49 | 118 | 86.8 | Capped Score | 6 |
| 41 | Travis Etienne | RB |  | NO | 36.33 | 46 | 59.5 | Capped Score | 9 |
| 42 | Emeka Egbuka | WR |  | TB | 36.31 | 58 | 27.1 | Capped Score | 5 |
| 43 | Jaylen Warren | RB |  | PIT | 34.2 | 65 | 107.6 | Capped Score | 8 |
| 44 | Parker Washington | WR |  | JAX | 34.11 | 114 | 101.6 | Capped Score | 7 |
| 45 | Brock Bowers | TE |  | LV | 34.02 | 21 | 11.7 | Capped Score | 7 |
| 46 | Ashton Jeanty | RB |  | LV | 33.77 | 16 | 9.8 | Capped Score | 6 |
| 47 | Davante Adams | WR |  | LAR | 33.11 | 36 | 85.3 | Capped Score | 6 |
| 48 | Rome Odunze | WR |  | CHI | 33.02 | 67 | 47.3 | Capped Score | 4 |
| 49 | Jalen Hurts | QB |  | PHI | 33.0 | 59 | 50.4 | Capped Score | 3 |
| 50 | Justin Herbert | QB |  | LAC | 33.0 | 71 | 69.5 | Scored + Warnings | 2 |

## Bottom 50 Scored Non-Kickers

| Rank | Player | Pos | Age | Team | Score | League | Market | Trust | Warnings |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| 232 | Kaleb Johnson | RB |  | PIT | 3.07 | 131 | 201.1 | Capped Score | 7 |
| 231 | Zach Ertz | TE |  |  | 4.09 | 400 | 537.0 | Capped Score | 10 |
| 230 | Roschon Johnson | RB |  | CHI | 4.36 | 400 |  | Capped Score | 5 |
| 229 | Jaydon Blue | RB |  | DAL | 4.79 | 288 | 196.1 | Capped Score | 7 |
| 228 | MarShawn Lloyd | RB |  | GB | 4.93 | 255 | 329.2 | Capped Score | 7 |
| 227 | Jonathon Brooks | RB |  | CAR | 5.54 | 176 | 125.3 | Capped Score | 6 |
| 226 | Darren Waller | TE |  |  | 5.81 | 304 | 539.5 | Capped Score | 10 |
| 225 | Tank Bigsby | RB |  | PHI | 6.31 | 135 | 179.5 | Capped Score | 7 |
| 224 | Braelon Allen | RB |  | NYJ | 6.51 | 102 | 158.3 | Capped Score | 7 |
| 223 | Nick Chubb | RB |  |  | 6.66 | 297 | 293.0 | Capped Score | 9 |
| 222 | Jeremy McNichols | RB |  | WAS | 6.91 | 400 |  | Capped Score | 8 |
| 221 | LeQuint Allen | RB |  | JAX | 7.0 | 290 | 242.5 | Capped Score | 4 |
| 220 | Keaton Mitchell | RB |  | LAC | 7.44 | 158 | 188.4 | Capped Score | 7 |
| 219 | Jaleel McLaughlin | RB |  | DEN | 7.54 | 223 |  | Capped Score | 7 |
| 218 | Emari Demercado | RB |  | KC | 7.61 | 283 | 539.5 | Capped Score | 9 |
| 217 | Sean Tucker | RB |  | TB | 7.99 | 178 | 229.1 | Capped Score | 5 |
| 216 | Bhayshul Tuten | RB |  | JAX | 8.08 | 76 | 74.3 | Capped Score | 6 |
| 215 | Kendre Miller | RB |  | NO | 8.13 | 156 | 305.8 | Capped Score | 6 |
| 214 | Zonovan Knight | RB |  | ARI | 8.28 | 250 |  | Capped Score | 11 |
| 213 | James Conner | RB |  | ARI | 8.42 | 96 | 209.2 | Capped Score | 8 |
| 212 | Brashard Smith | RB |  | KC | 8.66 | 256 | 280.2 | Capped Score | 6 |
| 211 | Kyler Murray | QB |  | MIN | 8.66 | 143 | 182.3 | Capped Score | 3 |
| 210 | Kareem Hunt | RB |  |  | 8.78 | 289 | 675.0 | Capped Score | 9 |
| 209 | Michael Penix | QB |  | ATL | 8.85 | 200 | 185.0 | Capped Score | 6 |
| 208 | Ollie Gordon | RB |  | MIA | 8.86 | 222 | 220.1 | Capped Score | 4 |
| 207 | Najee Harris | RB |  |  | 9.16 | 229 | 268.1 | Capped Score | 9 |
| 206 | Devin Neal | RB |  | NO | 9.26 | 179 | 213.0 | Capped Score | 5 |
| 205 | Shedeur Sanders | QB |  | CLE | 9.35 | 248 | 272.7 | Scored + Warnings | 2 |
| 204 | Ray Davis | RB |  | BUF | 9.35 | 205 | 233.4 | Capped Score | 6 |
| 203 | Elijah Arroyo | TE |  | SEA | 9.39 | 320 | 232.2 | Capped Score | 7 |
| 202 | Savion Williams | WR |  | GB | 9.44 | 400 | 487.0 | Capped Score | 5 |
| 201 | Isaiah Davis | RB |  | NYJ | 9.64 | 220 | 331.9 | Capped Score | 6 |
| 200 | Brian Robinson | RB |  | ATL | 9.7 | 159 | 191.9 | Capped Score | 9 |
| 199 | Joe Burrow | QB |  | CIN | 9.89 | 39 | 23.5 | Capped Score | 3 |
| 198 | Emanuel Wilson | RB |  | SEA | 10.12 | 185 | 227.5 | Capped Score | 9 |
| 197 | Justin Fields | QB |  | KC | 10.15 | 400 | 321.4 | Capped Score | 4 |
| 196 | Justice Hill | RB |  | BAL | 10.21 | 279 | 304.4 | Capped Score | 8 |
| 195 | Evan Engram | TE |  | DEN | 10.62 | 265 | 266.0 | Capped Score | 9 |
| 194 | J.J. McCarthy | QB |  | MIN | 10.72 | 155 | 250.7 | Scored + Warnings | 2 |
| 193 | Blake Corum | RB |  | LAR | 10.76 | 69 | 103.9 | Capped Score | 6 |
| 192 | Trey Benson | RB |  | ARI | 10.87 | 132 | 142.6 | Capped Score | 5 |
| 191 | Aaron Rodgers | QB |  | PIT | 10.99 | 311 | 301.5 | Capped Score | 4 |
| 190 | Isaiah Likely | TE |  | NYG | 11.03 | 183 | 117.2 | Capped Score | 7 |
| 189 | Alvin Kamara | RB |  | NO | 11.08 | 126 | 200.0 | Capped Score | 8 |
| 188 | Isaac TeSlaa | WR |  | DET | 11.09 | 175 | 195.1 | Capped Score | 5 |
| 187 | Chris Rodriguez | RB |  | JAX | 11.15 | 161 | 170.7 | Capped Score | 5 |
| 186 | Dylan Sampson | RB |  | CLE | 11.33 | 140 | 155.5 | Capped Score | 6 |
| 185 | Brock Purdy | QB |  | SF | 11.34 | 90 | 98.6 | Capped Score | 3 |
| 184 | Aaron Jones | RB |  | MIN | 11.34 | 99 | 161.3 | Capped Score | 8 |
| 183 | David Njoku | TE |  | LAC | 11.42 | 231 | 215.2 | Capped Score | 8 |

## My Team Movement

| Player | Pos | Age | Team | Old Score | New Score | Delta | New Rank | League | Market | Trust | Warnings | Movement Concern | Data/Source Concern | Human Review Question |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- |
| De'Von Achane | RB |  | MIA | 66.6696 | 61.33 | -5.3374 | 9 | 10 | 20.4 | Capped Score | 4 | none from movement audit | source warnings present | Are the confidence caps/warnings acceptable for review use? |
| Chase Brown | RB |  | CIN | 58.299 | 49.19 | -9.1097 | 24 | 35 | 35.3 | Capped Score | 4 | none from movement audit | source warnings present | Are the confidence caps/warnings acceptable for review use? |
| Wan'Dale Robinson | WR |  | TEN | 43.4188 | 36.49 | -6.9285 | 40 | 118 | 86.8 | Capped Score | 6 | warning_changed | identity/team evidence | Does the new full-board placement match football judgment? |
| Jakobi Meyers | WR |  | JAX | 31.5686 | 28.36 | -3.2107 | 64 | 95 | 113.7 | Capped Score | 6 | warning_changed | identity/team evidence | Does the new full-board placement match football judgment? |
| Quentin Johnston | WR |  | LAC | 35.5788 | 27.15 | -8.4245 | 68 | 94 | 105.8 | Capped Score | 5 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Jerry Jeudy | WR |  | CLE | 31.1199 | 26.86 | -4.2603 | 71 | 152 | 205.6 | Capped Score | 5 | none from movement audit | source warnings present | Are the confidence caps/warnings acceptable for review use? |
| Brian Thomas | WR |  | JAX | 32.3993 | 24.69 | -7.706 | 82 | 66 | 62.7 | Capped Score | 6 | warning_changed | source warnings present | Does the new full-board placement match football judgment? |
| Brandon Aiyuk | WR |  | SF | 25.4061 | 24.13 | -1.2737 | 84 | 98 | 159.9 | Capped Score | 4 | none from movement audit | source warnings present | Are the confidence caps/warnings acceptable for review use? |
| Luther Burden | WR |  | CHI | 31.3625 | 23.99 | -7.3713 | 85 | 56 | 46.3 | Capped Score | 6 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Jake Ferguson | TE |  | DAL | 41.1387 | 23.89 | -17.2459 | 86 | 109 | 104.4 | Capped Score | 7 | large_score_down | source warnings present | Does the new full-board placement match football judgment? |
| Ricky Pearsall | WR |  | SF | 25.9408 | 23.74 | -2.2049 | 87 | 91 | 93.8 | Capped Score | 6 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Romeo Doubs | WR |  | NE | 31.3334 | 23.39 | -7.9409 | 92 | 172 | 122.8 | Capped Score | 6 | large_rank_down | identity/team evidence | Does the new full-board placement match football judgment? |
| Xavier Worthy | WR |  | KC | 27.9883 | 22.28 | -5.71 | 98 | 133 | 116.4 | Capped Score | 4 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Jalen Coker | WR |  | CAR | 22.2108 | 18.76 | -3.4539 | 116 | 147 | 137.2 | Capped Score | 4 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Jayden Higgins | WR |  | HOU | 25.2852 | 17.89 | -7.3963 | 120 | 113 | 111.6 | Capped Score | 4 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| David Montgomery | RB |  | HOU | 35.0486 | 17.45 | -17.5989 | 121 | 97 | 79.2 | Capped Score | 7 | large_score_down | identity/team evidence | Does the new full-board placement match football judgment? |
| Oronde Gadsden | TE |  | LAC | 24.0072 | 17.13 | -6.8756 | 125 | 104 | 83.8 | Capped Score | 8 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Lamar Jackson | QB |  | BAL | 40.3535 | 15.09 | -25.26 | 144 | 31 | 26.0 | Scored + Warnings | 3 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |
| T.J. Hockenson | TE |  | MIN | 13.7788 | 14.16 | 0.379 | 155 | 206 | 184.7 | Capped Score | 7 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Brenton Strange | TE |  | JAX | 23.1507 | 13.93 | -9.2167 | 159 | 125 | 121.7 | Capped Score | 6 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Luke McCaffrey | WR |  | WAS | 16.2148 | 13.03 | -3.1869 | 166 | 263 | 529.3 | Capped Score | 5 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Devin Singletary | RB |  | NYG | 23.9309 | 12.5 | -11.4305 | 172 | 268 | 676.0 | Capped Score | 7 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |
| Daniel Jones | QB |  | IND | 31.312 | 11.61 | -19.6978 | 179 | 246 | 230.8 | Capped Score | 3 | suspicious_needs_review | identity/team evidence | Does the new full-board placement match football judgment? |
| Kaleb Johnson | RB |  | PIT | 3.0698 | 3.07 | 0.0 | 232 | 131 | 201.1 | Capped Score | 7 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |

## Biggest Score Risers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Jayden Daniels | QB | 8.9902 | 11.514 | 2.5238 | 74 | 180 | 106 | suspicious_needs_review | high |
| T.J. Hockenson | TE | 13.7788 | 14.1578 | 0.379 | 71 | 155 | 84 | large_rank_down | medium |
| Malik Nabers | WR | 30.4824 | 30.1846 | -0.2978 | 53 | 58 | 5 | stable | low |
| Jaxon Smith-Njigba | WR | 82.8713 | 82.5714 | -0.2999 | 3 | 2 | -1 | stable | low |
| Brandon Aiyuk | WR | 25.4061 | 24.1324 | -1.2737 | 60 | 84 | 24 | expected_universe_expansion | low |
| Bijan Robinson | RB | 79.9939 | 78.4618 | -1.5321 | 7 | 3 | -4 | expected_universe_expansion | low |
| Joe Burrow | QB | 11.9641 | 9.8866 | -2.0775 | 72 | 199 | 127 | suspicious_needs_review | high |
| Ricky Pearsall | WR | 25.9408 | 23.7359 | -2.2049 | 59 | 87 | 28 | expected_universe_expansion | medium |
| Garrett Wilson | WR | 31.5335 | 29.0057 | -2.5278 | 47 | 63 | 16 | expected_universe_expansion | low |
| Amon-Ra St. Brown | WR | 68.5918 | 65.9348 | -2.657 | 10 | 7 | -3 | expected_universe_expansion | low |
| George Pickens | WR | 62.9783 | 60.0258 | -2.9525 | 15 | 10 | -5 | warning_changed | medium |
| Luke McCaffrey | WR | 16.2148 | 13.0279 | -3.1869 | 70 | 166 | 96 | large_rank_down | medium |
| Jakobi Meyers | WR | 31.5686 | 28.3579 | -3.2107 | 46 | 64 | 18 | warning_changed | medium |
| Jahmyr Gibbs | RB | 73.9972 | 70.7273 | -3.2699 | 9 | 5 | -4 | expected_universe_expansion | low |
| Jalen Coker | WR | 22.2108 | 18.7569 | -3.4539 | 67 | 116 | 49 | large_rank_down | medium |
| Ja'Marr Chase | WR | 74.1258 | 70.5399 | -3.5859 | 8 | 6 | -2 | expected_universe_expansion | low |
| James Cook | RB | 63.7724 | 59.664 | -4.1084 | 14 | 11 | -3 | expected_universe_expansion | low |
| Jerry Jeudy | WR | 31.1199 | 26.8596 | -4.2603 | 52 | 71 | 19 | expected_universe_expansion | low |
| Drake London | WR | 57.2578 | 52.4925 | -4.7653 | 24 | 19 | -5 | expected_universe_expansion | low |
| CeeDee Lamb | WR | 56.2217 | 51.0992 | -5.1225 | 26 | 20 | -6 | expected_universe_expansion | low |

## Biggest Score Fallers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Travis Kelce | TE | 57.1755 | 14.7571 | -42.4184 | 25 | 150 | 125 | suspicious_needs_review | high |
| Derrick Henry | RB | 66.2156 | 28.3132 | -37.9024 | 12 | 65 | 53 | suspicious_needs_review | high |
| Patrick Mahomes | QB | 61.5482 | 27.5 | -34.0482 | 16 | 67 | 51 | suspicious_needs_review | high |
| Jalen Hurts | QB | 65.098 | 33.0 | -32.098 | 13 | 49 | 36 | suspicious_needs_review | high |
| Josh Allen | QB | 80.3133 | 50.3163 | -29.997 | 5 | 21 | 16 | suspicious_needs_review | high |
| Christian McCaffrey | RB | 82.8329 | 53.0131 | -29.8198 | 4 | 18 | 14 | suspicious_needs_review | high |
| Lamar Jackson | QB | 40.3535 | 15.0935 | -25.26 | 38 | 144 | 106 | suspicious_needs_review | high |
| Trey McBride | TE | 87.4776 | 62.2578 | -25.2198 | 1 | 8 | 7 | suspicious_needs_review | high |
| Davante Adams | WR | 57.5485 | 33.1056 | -24.4429 | 23 | 47 | 24 | large_score_down | medium |
| Keenan Allen | WR | 41.6097 | 17.2422 | -24.3675 | 36 | 124 | 88 | sentinel_watch | medium |
| Saquon Barkley | RB | 60.8166 | 38.08 | -22.7366 | 18 | 38 | 20 | large_score_down | medium |
| Daniel Jones | QB | 31.312 | 11.6142 | -19.6978 | 51 | 179 | 128 | suspicious_needs_review | high |
| Kenneth Walker III | RB | 44.6326 | 26.7476 | -17.885 | 33 | 73 | 40 | identity_or_team_changed | medium |
| David Montgomery | RB | 35.0486 | 17.4497 | -17.5989 | 42 | 121 | 79 | large_score_down | medium |
| George Kittle | TE | 32.0994 | 14.7218 | -17.3776 | 45 | 151 | 106 | suspicious_needs_review | high |
| Josh Jacobs | RB | 58.5387 | 41.2427 | -17.296 | 21 | 32 | 11 | large_score_down | medium |
| Jake Ferguson | TE | 41.1387 | 23.8928 | -17.2459 | 37 | 86 | 49 | large_score_down | medium |
| Brock Bowers | TE | 50.0029 | 34.0184 | -15.9845 | 29 | 45 | 16 | large_score_down | medium |
| Stefon Diggs | WR | 45.2808 | 29.8307 | -15.4501 | 32 | 61 | 29 | large_score_down | medium |
| Cooper Kupp | WR | 26.4622 | 14.6852 | -11.777 | 58 | 152 | 94 | large_rank_down | medium |

## Biggest Rank Risers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Chris Olave | WR | 59.4933 | 54.0656 | -5.4277 | 20 | 14 | -6 | expected_universe_expansion | low |
| CeeDee Lamb | WR | 56.2217 | 51.0992 | -5.1225 | 26 | 20 | -6 | expected_universe_expansion | low |
| George Pickens | WR | 62.9783 | 60.0258 | -2.9525 | 15 | 10 | -5 | warning_changed | medium |
| Drake London | WR | 57.2578 | 52.4925 | -4.7653 | 24 | 19 | -5 | expected_universe_expansion | low |
| Justin Jefferson | WR | 55.6738 | 50.2511 | -5.4227 | 27 | 22 | -5 | expected_universe_expansion | low |
| Bijan Robinson | RB | 79.9939 | 78.4618 | -1.5321 | 7 | 3 | -4 | expected_universe_expansion | low |
| Jahmyr Gibbs | RB | 73.9972 | 70.7273 | -3.2699 | 9 | 5 | -4 | expected_universe_expansion | low |
| Amon-Ra St. Brown | WR | 68.5918 | 65.9348 | -2.657 | 10 | 7 | -3 | expected_universe_expansion | low |
| James Cook | RB | 63.7724 | 59.664 | -4.1084 | 14 | 11 | -3 | expected_universe_expansion | low |
| Nico Collins | WR | 59.7382 | 53.4085 | -6.3297 | 19 | 16 | -3 | expected_universe_expansion | low |
| Jonathan Taylor | RB | 80.1465 | 74.308 | -5.8385 | 6 | 4 | -2 | warning_changed | medium |
| Ja'Marr Chase | WR | 74.1258 | 70.5399 | -3.5859 | 8 | 6 | -2 | expected_universe_expansion | low |
| De'Von Achane | RB | 66.6696 | 61.3322 | -5.3374 | 11 | 9 | -2 | expected_universe_expansion | low |
| Kyren Williams | RB | 61.1255 | 53.9777 | -7.1478 | 17 | 15 | -2 | expected_universe_expansion | low |
| Puka Nacua | WR | 83.0486 | 83.0486 | 0.0 | 2 | 1 | -1 | stable | low |
| Jaxon Smith-Njigba | WR | 82.8713 | 82.5714 | -0.2999 | 3 | 2 | -1 | stable | low |
| Chase Brown | RB | 58.299 | 49.1893 | -9.1097 | 22 | 24 | 2 | expected_universe_expansion | low |
| Breece Hall | RB | 53.4482 | 41.9244 | -11.5238 | 28 | 31 | 3 | expected_universe_expansion | medium |
| Jaylen Waddle | WR | 48.2068 | 41.1687 | -7.0381 | 30 | 33 | 3 | identity_or_team_changed | medium |
| Tee Higgins | WR | 45.5174 | 39.0127 | -6.5047 | 31 | 35 | 4 | expected_universe_expansion | low |

## Biggest Rank Fallers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Kaleb Johnson | RB | 3.0698 | 3.0698 | 0.0 | 75 | 232 | 157 | suspicious_needs_review | high |
| Daniel Jones | QB | 31.312 | 11.6142 | -19.6978 | 51 | 179 | 128 | suspicious_needs_review | high |
| Joe Burrow | QB | 11.9641 | 9.8866 | -2.0775 | 72 | 199 | 127 | suspicious_needs_review | high |
| Travis Kelce | TE | 57.1755 | 14.7571 | -42.4184 | 25 | 150 | 125 | suspicious_needs_review | high |
| Brock Purdy | QB | 21.3779 | 11.3396 | -10.0383 | 68 | 185 | 117 | suspicious_needs_review | high |
| Mark Andrews | TE | 23.1327 | 11.4817 | -11.651 | 66 | 181 | 115 | suspicious_needs_review | high |
| Devin Singletary | RB | 23.9309 | 12.5004 | -11.4305 | 64 | 172 | 108 | suspicious_needs_review | high |
| Lamar Jackson | QB | 40.3535 | 15.0935 | -25.26 | 38 | 144 | 106 | suspicious_needs_review | high |
| George Kittle | TE | 32.0994 | 14.7218 | -17.3776 | 45 | 151 | 106 | suspicious_needs_review | high |
| Jayden Daniels | QB | 8.9902 | 11.514 | 2.5238 | 74 | 180 | 106 | suspicious_needs_review | high |
| Luke McCaffrey | WR | 16.2148 | 13.0279 | -3.1869 | 70 | 166 | 96 | large_rank_down | medium |
| Cooper Kupp | WR | 26.4622 | 14.6852 | -11.777 | 58 | 152 | 94 | large_rank_down | medium |
| Brenton Strange | TE | 23.1507 | 13.934 | -9.2167 | 65 | 159 | 94 | large_rank_down | medium |
| Keenan Allen | WR | 41.6097 | 17.2422 | -24.3675 | 36 | 124 | 88 | sentinel_watch | medium |
| T.J. Hockenson | TE | 13.7788 | 14.1578 | 0.379 | 71 | 155 | 84 | large_rank_down | medium |
| David Montgomery | RB | 35.0486 | 17.4497 | -17.5989 | 42 | 121 | 79 | large_score_down | medium |
| Sam LaPorta | TE | 24.2632 | 15.3117 | -8.9515 | 62 | 141 | 79 | large_rank_down | medium |
| Mike Evans | WR | 28.4015 | 16.6866 | -11.7149 | 55 | 130 | 75 | identity_or_team_changed | medium |
| Oronde Gadsden II | TE | 24.0072 | 17.1316 | -6.8756 | 63 | 125 | 62 | large_rank_down | medium |
| Jayden Higgins | WR | 25.2852 | 17.8889 | -7.3963 | 61 | 120 | 59 | large_rank_down | medium |

## High League Rank With Lower NWR Rank

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| TreVeyon Henderson | RB |  | NE | 101 | 21.65 | 34 | 29.6 | Capped Score | 6 | source issue |
| Bucky Irving | RB |  | TB | 108 | 20.27 | 33 | 33.8 | Capped Score | 5 | source issue |
| Omarion Hampton | RB |  | LAC | 134 | 16.3 | 22 | 18.0 | Capped Score | 6 | source issue |
| Lamar Jackson | QB |  | BAL | 144 | 15.09 | 31 | 26.0 | Scored + Warnings | 3 | market disagreement only |
| Joe Burrow | QB |  | CIN | 199 | 9.89 | 39 | 23.5 | Capped Score | 3 | source issue |

## High NWR Rank With Lower League Or Market Rank

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Kyle Pitts | TE |  | ATL | 17 | 53.34 | 92 | 70.8 | Capped Score | 5 | source issue |
| Alec Pierce | WR |  | IND | 27 | 47.95 | 82 | 76.1 | Capped Score | 4 | source issue |
| Trevor Lawrence | QB |  | JAX | 28 | 47.44 | 84 | 91.9 | Scored + Warnings | 1 | market disagreement only |
| Courtland Sutton | WR |  | DEN | 29 | 42.94 | 55 | 109.0 | Capped Score | 5 | source issue |
| Michael Wilson | WR |  | ARI | 34 | 40.19 | 86 | 77.0 | Capped Score | 4 | source issue |
| DK Metcalf | WR |  | PIT | 36 | 38.9 | 60 | 89.1 | Capped Score | 6 | identity/team issue |
| Wan'Dale Robinson | WR |  | TEN | 40 | 36.49 | 118 | 86.8 | Capped Score | 6 | identity/team issue |

## Many Warnings But High NWR Score

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Jonathan Taylor | RB |  | IND | 4 | 74.31 | 7 | 16.5 | Capped Score | 6 | source issue |

## Low Trust Or Source Warnings But High NWR Rank

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Puka Nacua | WR |  | LAR | 1 | 83.05 | 2 | 3.7 | Capped Score | 4 | source issue |
| Jaxon Smith-Njigba | WR |  | SEA | 2 | 82.57 | 5 | 7.7 | Capped Score | 4 | source issue |
| Bijan Robinson | RB |  | ATL | 3 | 78.46 | 1 | 2.7 | Capped Score | 4 | source issue |
| Jonathan Taylor | RB |  | IND | 4 | 74.31 | 7 | 16.5 | Capped Score | 6 | source issue |
| Jahmyr Gibbs | RB |  | DET | 5 | 70.73 | 3 | 4.0 | Capped Score | 4 | source issue |
| Ja'Marr Chase | WR |  | CIN | 6 | 70.54 | 4 | 1.7 | Capped Score | 4 | source issue |
| Amon-Ra St. Brown | WR |  | DET | 7 | 65.93 | 8 | 5.4 | Capped Score | 6 | source issue |
| Trey McBride | TE |  | ARI | 8 | 62.26 | 17 | 14.9 | Capped Score | 5 | source issue |
| De'Von Achane | RB |  | MIA | 9 | 61.33 | 10 | 20.4 | Capped Score | 4 | source issue |
| George Pickens | WR |  | DAL | 10 | 60.03 | 18 | 22.9 | Capped Score | 5 | identity/team issue |
| James Cook | RB |  | BUF | 11 | 59.66 | 13 | 19.2 | Capped Score | 4 | source issue |
| Zay Flowers | WR |  | BAL | 12 | 56.53 | 43 | 51.0 | Capped Score | 4 | source issue |
| A.J. Brown | WR |  | PHI | 13 | 54.18 | 29 | 41.5 | Capped Score | 4 | source issue |
| Chris Olave | WR |  | NO | 14 | 54.07 | 25 | 29.9 | Capped Score | 5 | source issue |
| Kyren Williams | RB |  | LAR | 15 | 53.98 | 40 | 41.8 | Capped Score | 6 | source issue |
| Nico Collins | WR |  | HOU | 16 | 53.41 | 15 | 23.8 | Capped Score | 4 | source issue |
| Kyle Pitts | TE |  | ATL | 17 | 53.34 | 92 | 70.8 | Capped Score | 5 | source issue |
| Christian McCaffrey | RB |  | SF | 18 | 53.01 | 6 | 25.5 | Capped Score | 7 | source issue |
| Drake London | WR |  | ATL | 19 | 52.49 | 11 | 17.8 | Capped Score | 4 | source issue |
| CeeDee Lamb | WR |  | DAL | 20 | 51.1 | 9 | 13.7 | Capped Score | 5 | source issue |
| Josh Allen | QB |  | BUF | 21 | 50.32 | 24 | 8.0 | Capped Score | 3 | source issue |
| Justin Jefferson | WR |  | MIN | 22 | 50.25 | 19 | 11.8 | Capped Score | 5 | source issue |
| Drake Maye | QB |  | NE | 23 | 49.35 | 27 | 15.8 | Scored + Warnings | 2 | needs human football review |
| Chase Brown | RB |  | CIN | 24 | 49.19 | 35 | 35.3 | Capped Score | 4 | source issue |
| DeVonta Smith | WR |  | PHI | 25 | 48.62 | 61 | 65.8 | Capped Score | 4 | source issue |

## Sentinel And Contamination Checks

| Player | Current NWR | Legacy Score | Lineage | Source Column | Status |
| --- | ---: | ---: | --- | --- | --- |
| Keenan Allen | 17.24 | 82.4 | review_v4_current_player | checkpoint_review_score | comparison-only legacy preserved |
| Darius Slayton | 23.61 | 78.88 | review_v4_current_player | checkpoint_review_score | comparison-only legacy preserved |

- Legacy active-pack private_score used as NWR Dynasty Score: no.
- Market rank, league rank, ADP, startup, projection, consensus, or trade calculator used as NWR Dynasty Score: no.
- Market Rank and League Rank remain display-only comparison context.
- Risk remains legacy/display-only in the service and is not a default Model v4 private risk input.
- K rows remain the only unscored rows and are hidden by default in Rankings.
- Outcome percentages remain blank/in-development; no percentages were invented.

## Source And Identity Issues

- Team/identity movement rows: 3.
- Source Repair Needed rows: 8.
- Source Repair Needed position count: QB=0, RB=0, WR=0, TE=0.
- Team-change sample: Jaylen Waddle, Kenneth Walker III, Mike Evans.

## Final Audit Verdict

**full_board_rankings_ready_for_human_review**

Recommended next task: human review the movement audit and Dynasty Rankings top/bottom lists before any formula-candidate queue is opened.
