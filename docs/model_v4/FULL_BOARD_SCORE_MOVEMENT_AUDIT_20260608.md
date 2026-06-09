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
| large_score_movers | 9 |
| large_rank_movers | 27 |
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
| QB | 28 | 8.66 | 50.32 | 20.89 | 15.1 |
| RB | 79 | 3.07 | 82.83 | 22.86 | 15.21 |
| WR | 93 | 9.44 | 83.05 | 29.91 | 24.69 |
| TE | 32 | 9.39 | 62.26 | 20.76 | 14.48 |

### Full Board Score Bands

| Band | Count |
| --- | ---: |
| 80+ | 3 |
| 70-79.99 | 4 |
| 60-69.99 | 5 |
| 50-59.99 | 10 |
| 40-49.99 | 17 |
| 30-39.99 | 26 |
| 20-29.99 | 52 |
| under 20 | 115 |

### Position Balance Flags

- Top 25 position count: QB=2, RB=9, WR=11, TE=3.
- Top 50 position count: QB=4, RB=18, WR=25, TE=3.
- Bottom 25 position count: QB=3, RB=20, WR=1, TE=1.
- No automatic position-balance blocker triggered; human football review still required.

## Top 50 Full Board Players

| Rank | Player | Pos | Age | Team | Score | League | Market | Trust | Warnings |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| 1 | Puka Nacua | WR |  | LAR | 83.05 | 2 | 3.7 | Capped Score | 4 |
| 2 | Christian McCaffrey | RB |  | SF | 82.83 | 6 | 25.5 | Capped Score | 5 |
| 3 | Jaxon Smith-Njigba | WR |  | SEA | 82.57 | 5 | 7.7 | Capped Score | 4 |
| 4 | Jonathan Taylor | RB |  | IND | 79.05 | 7 | 16.5 | Capped Score | 5 |
| 5 | Bijan Robinson | RB |  | ATL | 78.46 | 1 | 2.7 | Capped Score | 4 |
| 6 | Jahmyr Gibbs | RB |  | DET | 70.73 | 3 | 4.0 | Capped Score | 4 |
| 7 | Ja'Marr Chase | WR |  | CIN | 70.54 | 4 | 1.7 | Capped Score | 4 |
| 8 | Amon-Ra St. Brown | WR |  | DET | 65.93 | 8 | 5.4 | Capped Score | 6 |
| 9 | Trey McBride | TE |  | ARI | 62.26 | 17 | 14.9 | Capped Score | 5 |
| 10 | Derrick Henry | RB |  | BAL | 61.55 | 20 | 61.7 | Capped Score | 5 |
| 11 | De'Von Achane | RB |  | MIA | 61.33 | 10 | 20.4 | Capped Score | 4 |
| 12 | George Pickens | WR |  | DAL | 60.03 | 18 | 22.9 | Capped Score | 5 |
| 13 | James Cook | RB |  | BUF | 59.66 | 13 | 19.2 | Capped Score | 4 |
| 14 | Zay Flowers | WR |  | BAL | 56.53 | 43 | 51.0 | Capped Score | 4 |
| 15 | A.J. Brown | WR |  | PHI | 54.18 | 29 | 41.5 | Capped Score | 4 |
| 16 | Chris Olave | WR |  | NO | 54.07 | 25 | 29.9 | Capped Score | 5 |
| 17 | Kyren Williams | RB |  | LAR | 53.98 | 40 | 41.8 | Capped Score | 6 |
| 18 | Nico Collins | WR |  | HOU | 53.41 | 15 | 23.8 | Capped Score | 4 |
| 19 | Kyle Pitts | TE |  | ATL | 53.34 | 92 | 70.8 | Capped Score | 5 |
| 20 | Davante Adams | WR |  | LAR | 50.93 | 36 | 85.3 | Capped Score | 4 |
| 21 | Josh Allen | QB |  | BUF | 50.32 | 24 | 8.0 | Capped Score | 3 |
| 22 | Saquon Barkley | RB |  | PHI | 50.11 | 23 | 34.1 | Capped Score | 6 |
| 23 | Drake London | WR |  | ATL | 49.49 | 11 | 17.8 | Capped Score | 4 |
| 24 | Drake Maye | QB |  | NE | 49.35 | 27 | 15.8 | Scored + Warnings | 2 |
| 25 | Travis Kelce | TE |  | KC | 49.19 | 165 | 164.5 | Capped Score | 6 |
| 26 | Chase Brown | RB |  | CIN | 49.19 | 35 | 35.3 | Capped Score | 4 |
| 27 | CeeDee Lamb | WR |  | DAL | 48.6 | 9 | 13.7 | Capped Score | 5 |
| 28 | Jameson Williams | WR |  | DET | 48.49 | 37 | 63.2 | Capped Score | 5 |
| 29 | Josh Jacobs | RB |  | GB | 47.96 | 26 | 47.2 | Capped Score | 6 |
| 30 | Justin Jefferson | WR |  | MIN | 47.75 | 19 | 11.8 | Capped Score | 5 |
| 31 | Trevor Lawrence | QB |  | JAX | 47.44 | 84 | 91.9 | Scored + Warnings | 1 |
| 32 | DeVonta Smith | WR |  | PHI | 45.62 | 61 | 65.8 | Capped Score | 4 |
| 33 | Alec Pierce | WR |  | IND | 44.95 | 82 | 76.1 | Capped Score | 4 |
| 34 | Courtland Sutton | WR |  | DEN | 44.73 | 55 | 109.0 | Capped Score | 4 |
| 35 | Tetairoa McMillan | WR |  | CAR | 42.83 | 30 | 21.2 | Capped Score | 4 |
| 36 | Breece Hall | RB |  | NYJ | 41.92 | 32 | 43.3 | Capped Score | 5 |
| 37 | Jaylen Waddle | WR |  | DEN | 41.17 | 44 | 67.2 | Capped Score | 5 |
| 38 | Michael Wilson | WR |  | ARI | 40.19 | 86 | 77.0 | Capped Score | 4 |
| 39 | D'Andre Swift | RB |  | CHI | 40.01 | 62 | 75.0 | Capped Score | 7 |
| 40 | Tee Higgins | WR |  | CIN | 39.01 | 28 | 55.9 | Capped Score | 4 |
| 41 | DK Metcalf | WR |  | PIT | 38.9 | 60 | 89.1 | Capped Score | 6 |
| 42 | Javonte Williams | RB |  | DAL | 38.87 | 52 | 56.9 | Capped Score | 7 |
| 43 | Travis Etienne | RB |  | NO | 38.65 | 46 | 59.5 | Capped Score | 8 |
| 44 | Stefon Diggs | WR |  |  | 38.24 | 89 | 167.0 | Capped Score | 5 |
| 45 | Matthew Stafford | QB |  | LAR | 37.12 | 103 | 176.3 | Scored + Warnings | 2 |
| 46 | Wan'Dale Robinson | WR |  | TEN | 36.49 | 118 | 86.8 | Capped Score | 6 |
| 47 | Jaylen Warren | RB |  | PIT | 36.39 | 65 | 107.6 | Capped Score | 7 |
| 48 | Emeka Egbuka | WR |  | TB | 36.31 | 58 | 27.1 | Capped Score | 5 |
| 49 | Rico Dowdle | RB |  | PIT | 35.83 | 72 | 112.8 | Capped Score | 8 |
| 50 | Joe Mixon | RB |  |  | 35.73 | 142 | 342.0 | Capped Score | 7 |

## Bottom 50 Scored Non-Kickers

| Rank | Player | Pos | Age | Team | Score | League | Market | Trust | Warnings |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| 232 | Kaleb Johnson | RB |  | PIT | 3.07 | 131 | 201.1 | Capped Score | 7 |
| 231 | Roschon Johnson | RB |  | CHI | 4.36 | 400 |  | Capped Score | 5 |
| 230 | Jaydon Blue | RB |  | DAL | 4.79 | 288 | 196.1 | Capped Score | 7 |
| 229 | MarShawn Lloyd | RB |  | GB | 4.93 | 255 | 329.2 | Capped Score | 7 |
| 228 | Jonathon Brooks | RB |  | CAR | 5.54 | 176 | 125.3 | Capped Score | 6 |
| 227 | Tank Bigsby | RB |  | PHI | 6.31 | 135 | 179.5 | Capped Score | 7 |
| 226 | Braelon Allen | RB |  | NYJ | 6.51 | 102 | 158.3 | Capped Score | 7 |
| 225 | LeQuint Allen | RB |  | JAX | 7.0 | 290 | 242.5 | Capped Score | 4 |
| 224 | Keaton Mitchell | RB |  | LAC | 7.44 | 158 | 188.4 | Capped Score | 7 |
| 223 | Jaleel McLaughlin | RB |  | DEN | 7.54 | 223 |  | Capped Score | 7 |
| 222 | Sean Tucker | RB |  | TB | 7.99 | 178 | 229.1 | Capped Score | 5 |
| 221 | Bhayshul Tuten | RB |  | JAX | 8.08 | 76 | 74.3 | Capped Score | 6 |
| 220 | Emari Demercado | RB |  | KC | 8.09 | 283 | 539.5 | Capped Score | 8 |
| 219 | Kendre Miller | RB |  | NO | 8.13 | 156 | 305.8 | Capped Score | 6 |
| 218 | Zonovan Knight | RB |  | ARI | 8.28 | 250 |  | Capped Score | 11 |
| 217 | Brashard Smith | RB |  | KC | 8.66 | 256 | 280.2 | Capped Score | 6 |
| 216 | Kyler Murray | QB |  | MIN | 8.66 | 143 | 182.3 | Capped Score | 3 |
| 215 | Michael Penix | QB |  | ATL | 8.85 | 200 | 185.0 | Capped Score | 6 |
| 214 | Ollie Gordon | RB |  | MIA | 8.86 | 222 | 220.1 | Capped Score | 4 |
| 213 | Devin Neal | RB |  | NO | 9.26 | 179 | 213.0 | Capped Score | 5 |
| 212 | Shedeur Sanders | QB |  | CLE | 9.35 | 248 | 272.7 | Scored + Warnings | 2 |
| 211 | Ray Davis | RB |  | BUF | 9.35 | 205 | 233.4 | Capped Score | 6 |
| 210 | Elijah Arroyo | TE |  | SEA | 9.39 | 320 | 232.2 | Capped Score | 7 |
| 209 | Savion Williams | WR |  | GB | 9.44 | 400 | 487.0 | Capped Score | 5 |
| 208 | Isaiah Davis | RB |  | NYJ | 9.64 | 220 | 331.9 | Capped Score | 6 |
| 207 | Joe Burrow | QB |  | CIN | 9.89 | 39 | 23.5 | Capped Score | 3 |
| 206 | Justin Fields | QB |  | KC | 10.15 | 400 | 321.4 | Capped Score | 4 |
| 205 | Brian Robinson | RB |  | ATL | 10.32 | 159 | 191.9 | Capped Score | 8 |
| 204 | Nick Chubb | RB |  |  | 10.4 | 297 | 293.0 | Capped Score | 7 |
| 203 | Najee Harris | RB |  |  | 10.66 | 229 | 268.1 | Capped Score | 8 |
| 202 | J.J. McCarthy | QB |  | MIN | 10.72 | 155 | 250.7 | Scored + Warnings | 2 |
| 201 | Blake Corum | RB |  | LAR | 10.76 | 69 | 103.9 | Capped Score | 6 |
| 200 | Emanuel Wilson | RB |  | SEA | 10.77 | 185 | 227.5 | Capped Score | 8 |
| 199 | Jeremy McNichols | RB |  | WAS | 10.8 | 400 |  | Capped Score | 6 |
| 198 | Trey Benson | RB |  | ARI | 10.87 | 132 | 142.6 | Capped Score | 5 |
| 197 | Aaron Rodgers | QB |  | PIT | 10.99 | 311 | 301.5 | Capped Score | 4 |
| 196 | Isaiah Likely | TE |  | NYG | 11.03 | 183 | 117.2 | Capped Score | 7 |
| 195 | Isaac TeSlaa | WR |  | DET | 11.09 | 175 | 195.1 | Capped Score | 5 |
| 194 | Chris Rodriguez | RB |  | JAX | 11.15 | 161 | 170.7 | Capped Score | 5 |
| 193 | Darren Waller | TE |  |  | 11.17 | 304 | 539.5 | Capped Score | 8 |
| 192 | Dylan Sampson | RB |  | CLE | 11.33 | 140 | 155.5 | Capped Score | 6 |
| 191 | Brock Purdy | QB |  | SF | 11.34 | 90 | 98.6 | Capped Score | 3 |
| 190 | Gunnar Helm | TE |  | TEN | 11.48 | 244 | 190.3 | Capped Score | 7 |
| 189 | Jayden Daniels | QB |  | WAS | 11.51 | 47 | 31.8 | Scored + Warnings | 2 |
| 188 | Daniel Jones | QB |  | IND | 11.61 | 246 | 230.8 | Capped Score | 3 |
| 187 | Justice Hill | RB |  | BAL | 11.87 | 279 | 304.4 | Capped Score | 7 |
| 186 | Jacory Croskey-Merritt | RB |  | WAS | 11.89 | 83 | 115.9 | Capped Score | 5 |
| 185 | Sam Darnold | QB |  | SEA | 11.89 | 137 | 189.5 | Capped Score | 3 |
| 184 | Jaylin Noel | WR |  | HOU | 11.9 | 182 | 219.5 | Capped Score | 7 |
| 183 | Cole Kmet | TE |  | CHI | 12.18 | 400 | 323.9 | Capped Score | 6 |

## My Team Movement

| Player | Pos | Age | Team | Old Score | New Score | Delta | New Rank | League | Market | Trust | Warnings | Movement Concern | Data/Source Concern | Human Review Question |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- |
| De'Von Achane | RB |  | MIA | 66.6696 | 61.33 | -5.3374 | 11 | 10 | 20.4 | Capped Score | 4 | none from movement audit | source warnings present | Are the confidence caps/warnings acceptable for review use? |
| Chase Brown | RB |  | CIN | 58.299 | 49.19 | -9.1097 | 26 | 35 | 35.3 | Capped Score | 4 | none from movement audit | source warnings present | Are the confidence caps/warnings acceptable for review use? |
| Wan'Dale Robinson | WR |  | TEN | 43.4188 | 36.49 | -6.9285 | 46 | 118 | 86.8 | Capped Score | 6 | warning_changed | identity/team evidence | Does the new full-board placement match football judgment? |
| Jakobi Meyers | WR |  | JAX | 31.5686 | 28.36 | -3.2107 | 73 | 95 | 113.7 | Capped Score | 6 | warning_changed | identity/team evidence | Does the new full-board placement match football judgment? |
| Quentin Johnston | WR |  | LAC | 35.5788 | 27.15 | -8.4245 | 75 | 94 | 105.8 | Capped Score | 5 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Jerry Jeudy | WR |  | CLE | 31.1199 | 26.86 | -4.2603 | 78 | 152 | 205.6 | Capped Score | 5 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Brian Thomas | WR |  | JAX | 32.3993 | 24.69 | -7.706 | 86 | 66 | 62.7 | Capped Score | 6 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Brandon Aiyuk | WR |  | SF | 25.4061 | 24.13 | -1.2737 | 90 | 98 | 159.9 | Capped Score | 4 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Luther Burden | WR |  | CHI | 31.3625 | 23.99 | -7.3713 | 91 | 56 | 46.3 | Capped Score | 6 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Jake Ferguson | TE |  | DAL | 41.1387 | 23.89 | -17.2459 | 92 | 109 | 104.4 | Capped Score | 7 | large_score_down | source warnings present | Does the new full-board placement match football judgment? |
| Ricky Pearsall | WR |  | SF | 25.9408 | 23.74 | -2.2049 | 93 | 91 | 93.8 | Capped Score | 6 | expected_universe_expansion | source warnings present | Does the new full-board placement match football judgment? |
| Romeo Doubs | WR |  | NE | 31.3334 | 23.39 | -7.9409 | 96 | 172 | 122.8 | Capped Score | 6 | large_rank_down | identity/team evidence | Does the new full-board placement match football judgment? |
| David Montgomery | RB |  | HOU | 35.0486 | 22.96 | -12.0884 | 101 | 97 | 79.2 | Capped Score | 6 | large_rank_down | identity/team evidence | Does the new full-board placement match football judgment? |
| Xavier Worthy | WR |  | KC | 27.9883 | 22.28 | -5.71 | 105 | 133 | 116.4 | Capped Score | 4 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Jalen Coker | WR |  | CAR | 22.2108 | 18.76 | -3.4539 | 126 | 147 | 137.2 | Capped Score | 4 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Jayden Higgins | WR |  | HOU | 25.2852 | 17.89 | -7.3963 | 130 | 113 | 111.6 | Capped Score | 4 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Oronde Gadsden | TE |  | LAC | 24.0072 | 17.13 | -6.8756 | 133 | 104 | 83.8 | Capped Score | 8 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Lamar Jackson | QB |  | BAL | 40.3535 | 15.09 | -25.26 | 152 | 31 | 26.0 | Scored + Warnings | 3 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |
| Devin Singletary | RB |  | NYG | 23.9309 | 14.54 | -9.3955 | 159 | 268 | 676.0 | Capped Score | 6 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| T.J. Hockenson | TE |  | MIN | 13.7788 | 14.16 | 0.379 | 162 | 206 | 184.7 | Capped Score | 7 | large_rank_down | source warnings present | Does the new full-board placement match football judgment? |
| Brenton Strange | TE |  | JAX | 23.1507 | 13.93 | -9.2167 | 166 | 125 | 121.7 | Capped Score | 6 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |
| Luke McCaffrey | WR |  | WAS | 16.2148 | 13.03 | -3.1869 | 177 | 263 | 529.3 | Capped Score | 5 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |
| Daniel Jones | QB |  | IND | 31.312 | 11.61 | -19.6978 | 188 | 246 | 230.8 | Capped Score | 3 | suspicious_needs_review | identity/team evidence | Does the new full-board placement match football judgment? |
| Kaleb Johnson | RB |  | PIT | 3.0698 | 3.07 | 0.0 | 232 | 131 | 201.1 | Capped Score | 7 | suspicious_needs_review | source warnings present | Does the new full-board placement match football judgment? |

## Biggest Score Risers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Jayden Daniels | QB | 8.9902 | 11.514 | 2.5238 | 74 | 189 | 115 | suspicious_needs_review | high |
| T.J. Hockenson | TE | 13.7788 | 14.1578 | 0.379 | 71 | 162 | 91 | large_rank_down | medium |
| Malik Nabers | WR | 30.4824 | 30.1846 | -0.2978 | 53 | 65 | 12 | expected_universe_expansion | low |
| Jaxon Smith-Njigba | WR | 82.8713 | 82.5714 | -0.2999 | 3 | 3 | 0 | stable | low |
| Jonathan Taylor | RB | 80.1465 | 79.051 | -1.0955 | 6 | 4 | -2 | expected_universe_expansion | low |
| Brandon Aiyuk | WR | 25.4061 | 24.1324 | -1.2737 | 60 | 90 | 30 | expected_universe_expansion | medium |
| Bijan Robinson | RB | 79.9939 | 78.4618 | -1.5321 | 7 | 5 | -2 | expected_universe_expansion | low |
| Joe Burrow | QB | 11.9641 | 9.8866 | -2.0775 | 72 | 207 | 135 | suspicious_needs_review | high |
| Ricky Pearsall | WR | 25.9408 | 23.7359 | -2.2049 | 59 | 93 | 34 | expected_universe_expansion | medium |
| Garrett Wilson | WR | 31.5335 | 29.0057 | -2.5278 | 47 | 70 | 23 | expected_universe_expansion | low |
| Amon-Ra St. Brown | WR | 68.5918 | 65.9348 | -2.657 | 10 | 8 | -2 | expected_universe_expansion | low |
| Mike Evans | WR | 28.4015 | 25.6716 | -2.7299 | 55 | 84 | 29 | identity_or_team_changed | medium |
| George Pickens | WR | 62.9783 | 60.0258 | -2.9525 | 15 | 12 | -3 | warning_changed | medium |
| Luke McCaffrey | WR | 16.2148 | 13.0279 | -3.1869 | 70 | 177 | 107 | suspicious_needs_review | high |
| Jakobi Meyers | WR | 31.5686 | 28.3579 | -3.2107 | 46 | 73 | 27 | warning_changed | medium |
| Jahmyr Gibbs | RB | 73.9972 | 70.7273 | -3.2699 | 9 | 6 | -3 | expected_universe_expansion | low |
| Jalen Coker | WR | 22.2108 | 18.7569 | -3.4539 | 67 | 126 | 59 | large_rank_down | medium |
| Ja'Marr Chase | WR | 74.1258 | 70.5399 | -3.5859 | 8 | 7 | -1 | expected_universe_expansion | low |
| Cooper Kupp | WR | 26.4622 | 22.5926 | -3.8696 | 58 | 103 | 45 | large_rank_down | medium |
| James Cook | RB | 63.7724 | 59.664 | -4.1084 | 14 | 13 | -1 | expected_universe_expansion | low |

## Biggest Score Fallers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Patrick Mahomes | QB | 61.5482 | 24.1863 | -37.3619 | 16 | 89 | 73 | suspicious_needs_review | high |
| Jalen Hurts | QB | 65.098 | 28.7722 | -36.3258 | 13 | 71 | 58 | suspicious_needs_review | high |
| Josh Allen | QB | 80.3133 | 50.3163 | -29.997 | 5 | 21 | 16 | suspicious_needs_review | high |
| Lamar Jackson | QB | 40.3535 | 15.0935 | -25.26 | 38 | 152 | 114 | suspicious_needs_review | high |
| Trey McBride | TE | 87.4776 | 62.2578 | -25.2198 | 1 | 9 | 8 | suspicious_needs_review | high |
| Daniel Jones | QB | 31.312 | 11.6142 | -19.6978 | 51 | 188 | 137 | suspicious_needs_review | high |
| Kenneth Walker III | RB | 44.6326 | 26.7476 | -17.885 | 33 | 80 | 47 | identity_or_team_changed | medium |
| Jake Ferguson | TE | 41.1387 | 23.8928 | -17.2459 | 37 | 92 | 55 | large_score_down | medium |
| Brock Bowers | TE | 50.0029 | 34.0184 | -15.9845 | 29 | 54 | 25 | large_score_down | medium |
| David Montgomery | RB | 35.0486 | 22.9602 | -12.0884 | 42 | 101 | 59 | large_rank_down | medium |
| Breece Hall | RB | 53.4482 | 41.9244 | -11.5238 | 28 | 36 | 8 | expected_universe_expansion | medium |
| Saquon Barkley | RB | 60.8166 | 50.1053 | -10.7113 | 18 | 22 | 4 | expected_universe_expansion | medium |
| Josh Jacobs | RB | 58.5387 | 47.9566 | -10.5821 | 21 | 29 | 8 | expected_universe_expansion | medium |
| Ashton Jeanty | RB | 44.2641 | 33.7716 | -10.4925 | 34 | 55 | 21 | expected_universe_expansion | medium |
| Brock Purdy | QB | 21.3779 | 11.3396 | -10.0383 | 68 | 191 | 123 | suspicious_needs_review | high |
| George Kittle | TE | 32.0994 | 22.3058 | -9.7936 | 45 | 104 | 59 | large_rank_down | medium |
| Devin Singletary | RB | 23.9309 | 14.5354 | -9.3955 | 64 | 159 | 95 | large_rank_down | medium |
| Brenton Strange | TE | 23.1507 | 13.934 | -9.2167 | 65 | 166 | 101 | suspicious_needs_review | high |
| Chase Brown | RB | 58.299 | 49.1893 | -9.1097 | 22 | 26 | 4 | expected_universe_expansion | low |
| Sam LaPorta | TE | 24.2632 | 15.3117 | -8.9515 | 62 | 149 | 87 | large_rank_down | medium |

## Biggest Rank Risers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Chris Olave | WR | 59.4933 | 54.0656 | -5.4277 | 20 | 16 | -4 | expected_universe_expansion | low |
| Jahmyr Gibbs | RB | 73.9972 | 70.7273 | -3.2699 | 9 | 6 | -3 | expected_universe_expansion | low |
| George Pickens | WR | 62.9783 | 60.0258 | -2.9525 | 15 | 12 | -3 | warning_changed | medium |
| Davante Adams | WR | 57.5485 | 50.9317 | -6.6168 | 23 | 20 | -3 | expected_universe_expansion | low |
| Christian McCaffrey | RB | 82.8329 | 82.8329 | 0.0 | 4 | 2 | -2 | stable | low |
| Jonathan Taylor | RB | 80.1465 | 79.051 | -1.0955 | 6 | 4 | -2 | expected_universe_expansion | low |
| Bijan Robinson | RB | 79.9939 | 78.4618 | -1.5321 | 7 | 5 | -2 | expected_universe_expansion | low |
| Amon-Ra St. Brown | WR | 68.5918 | 65.9348 | -2.657 | 10 | 8 | -2 | expected_universe_expansion | low |
| Derrick Henry | RB | 66.2156 | 61.5505 | -4.6651 | 12 | 10 | -2 | expected_universe_expansion | low |
| Puka Nacua | WR | 83.0486 | 83.0486 | 0.0 | 2 | 1 | -1 | stable | low |
| Ja'Marr Chase | WR | 74.1258 | 70.5399 | -3.5859 | 8 | 7 | -1 | expected_universe_expansion | low |
| James Cook | RB | 63.7724 | 59.664 | -4.1084 | 14 | 13 | -1 | expected_universe_expansion | low |
| Nico Collins | WR | 59.7382 | 53.4085 | -6.3297 | 19 | 18 | -1 | expected_universe_expansion | low |
| Drake London | WR | 57.2578 | 49.4925 | -7.7653 | 24 | 23 | -1 | expected_universe_expansion | low |
| Jaxon Smith-Njigba | WR | 82.8713 | 82.5714 | -0.2999 | 3 | 3 | 0 | stable | low |
| De'Von Achane | RB | 66.6696 | 61.3322 | -5.3374 | 11 | 11 | 0 | expected_universe_expansion | low |
| Kyren Williams | RB | 61.1255 | 53.9777 | -7.1478 | 17 | 17 | 0 | expected_universe_expansion | low |
| Travis Kelce | TE | 57.1755 | 49.1903 | -7.9852 | 25 | 25 | 0 | warning_changed | medium |
| CeeDee Lamb | WR | 56.2217 | 48.5992 | -7.6225 | 26 | 27 | 1 | expected_universe_expansion | low |
| Justin Jefferson | WR | 55.6738 | 47.7511 | -7.9227 | 27 | 30 | 3 | expected_universe_expansion | low |

## Biggest Rank Fallers

| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | Rank Delta | Bucket | Severity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Kaleb Johnson | RB | 3.0698 | 3.0698 | 0.0 | 75 | 232 | 157 | suspicious_needs_review | high |
| Daniel Jones | QB | 31.312 | 11.6142 | -19.6978 | 51 | 188 | 137 | suspicious_needs_review | high |
| Joe Burrow | QB | 11.9641 | 9.8866 | -2.0775 | 72 | 207 | 135 | suspicious_needs_review | high |
| Brock Purdy | QB | 21.3779 | 11.3396 | -10.0383 | 68 | 191 | 123 | suspicious_needs_review | high |
| Jayden Daniels | QB | 8.9902 | 11.514 | 2.5238 | 74 | 189 | 115 | suspicious_needs_review | high |
| Lamar Jackson | QB | 40.3535 | 15.0935 | -25.26 | 38 | 152 | 114 | suspicious_needs_review | high |
| Luke McCaffrey | WR | 16.2148 | 13.0279 | -3.1869 | 70 | 177 | 107 | suspicious_needs_review | high |
| Brenton Strange | TE | 23.1507 | 13.934 | -9.2167 | 65 | 166 | 101 | suspicious_needs_review | high |
| Devin Singletary | RB | 23.9309 | 14.5354 | -9.3955 | 64 | 159 | 95 | large_rank_down | medium |
| Mark Andrews | TE | 23.1327 | 14.3521 | -8.7806 | 66 | 161 | 95 | large_rank_down | medium |
| T.J. Hockenson | TE | 13.7788 | 14.1578 | 0.379 | 71 | 162 | 91 | large_rank_down | medium |
| Sam LaPorta | TE | 24.2632 | 15.3117 | -8.9515 | 62 | 149 | 87 | large_rank_down | medium |
| Patrick Mahomes | QB | 61.5482 | 24.1863 | -37.3619 | 16 | 89 | 73 | suspicious_needs_review | high |
| Oronde Gadsden II | TE | 24.0072 | 17.1316 | -6.8756 | 63 | 133 | 70 | large_rank_down | medium |
| Jayden Higgins | WR | 25.2852 | 17.8889 | -7.3963 | 61 | 130 | 69 | large_rank_down | medium |
| Tank Dell | WR | 27.2878 | 19.0118 | -8.276 | 57 | 123 | 66 | large_rank_down | medium |
| David Montgomery | RB | 35.0486 | 22.9602 | -12.0884 | 42 | 101 | 59 | large_rank_down | medium |
| Jalen Coker | WR | 22.2108 | 18.7569 | -3.4539 | 67 | 126 | 59 | large_rank_down | medium |
| George Kittle | TE | 32.0994 | 22.3058 | -9.7936 | 45 | 104 | 59 | large_rank_down | medium |
| Jalen Hurts | QB | 65.098 | 28.7722 | -36.3258 | 13 | 71 | 58 | suspicious_needs_review | high |

## High League Rank With Lower NWR Rank

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Rashee Rice | WR |  | KC | 83 | 25.77 | 14 | 39.1 | Capped Score | 5 | source issue |
| TreVeyon Henderson | RB |  | NE | 108 | 21.65 | 34 | 29.6 | Capped Score | 6 | source issue |
| Bucky Irving | RB |  | TB | 117 | 20.27 | 33 | 33.8 | Capped Score | 5 | source issue |
| Omarion Hampton | RB |  | LAC | 141 | 16.3 | 22 | 18.0 | Capped Score | 6 | source issue |
| Lamar Jackson | QB |  | BAL | 152 | 15.09 | 31 | 26.0 | Scored + Warnings | 3 | market disagreement only |
| Joe Burrow | QB |  | CIN | 207 | 9.89 | 39 | 23.5 | Capped Score | 3 | source issue |

## High NWR Rank With Lower League Or Market Rank

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Kyle Pitts | TE |  | ATL | 19 | 53.34 | 92 | 70.8 | Capped Score | 5 | source issue |
| Davante Adams | WR |  | LAR | 20 | 50.93 | 36 | 85.3 | Capped Score | 4 | source issue |
| Travis Kelce | TE |  | KC | 25 | 49.19 | 165 | 164.5 | Capped Score | 6 | source issue |
| Trevor Lawrence | QB |  | JAX | 31 | 47.44 | 84 | 91.9 | Scored + Warnings | 1 | market disagreement only |
| Alec Pierce | WR |  | IND | 33 | 44.95 | 82 | 76.1 | Capped Score | 4 | source issue |
| Courtland Sutton | WR |  | DEN | 34 | 44.73 | 55 | 109.0 | Capped Score | 4 | source issue |
| Michael Wilson | WR |  | ARI | 38 | 40.19 | 86 | 77.0 | Capped Score | 4 | source issue |

## Many Warnings But High NWR Score

_No rows triggered this scan._

## Low Trust Or Source Warnings But High NWR Rank

| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | Warnings | Issue Bucket |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Puka Nacua | WR |  | LAR | 1 | 83.05 | 2 | 3.7 | Capped Score | 4 | source issue |
| Christian McCaffrey | RB |  | SF | 2 | 82.83 | 6 | 25.5 | Capped Score | 5 | source issue |
| Jaxon Smith-Njigba | WR |  | SEA | 3 | 82.57 | 5 | 7.7 | Capped Score | 4 | source issue |
| Jonathan Taylor | RB |  | IND | 4 | 79.05 | 7 | 16.5 | Capped Score | 5 | source issue |
| Bijan Robinson | RB |  | ATL | 5 | 78.46 | 1 | 2.7 | Capped Score | 4 | source issue |
| Jahmyr Gibbs | RB |  | DET | 6 | 70.73 | 3 | 4.0 | Capped Score | 4 | source issue |
| Ja'Marr Chase | WR |  | CIN | 7 | 70.54 | 4 | 1.7 | Capped Score | 4 | source issue |
| Amon-Ra St. Brown | WR |  | DET | 8 | 65.93 | 8 | 5.4 | Capped Score | 6 | source issue |
| Trey McBride | TE |  | ARI | 9 | 62.26 | 17 | 14.9 | Capped Score | 5 | source issue |
| Derrick Henry | RB |  | BAL | 10 | 61.55 | 20 | 61.7 | Capped Score | 5 | source issue |
| De'Von Achane | RB |  | MIA | 11 | 61.33 | 10 | 20.4 | Capped Score | 4 | source issue |
| George Pickens | WR |  | DAL | 12 | 60.03 | 18 | 22.9 | Capped Score | 5 | identity/team issue |
| James Cook | RB |  | BUF | 13 | 59.66 | 13 | 19.2 | Capped Score | 4 | source issue |
| Zay Flowers | WR |  | BAL | 14 | 56.53 | 43 | 51.0 | Capped Score | 4 | source issue |
| A.J. Brown | WR |  | PHI | 15 | 54.18 | 29 | 41.5 | Capped Score | 4 | source issue |
| Chris Olave | WR |  | NO | 16 | 54.07 | 25 | 29.9 | Capped Score | 5 | source issue |
| Kyren Williams | RB |  | LAR | 17 | 53.98 | 40 | 41.8 | Capped Score | 6 | source issue |
| Nico Collins | WR |  | HOU | 18 | 53.41 | 15 | 23.8 | Capped Score | 4 | source issue |
| Kyle Pitts | TE |  | ATL | 19 | 53.34 | 92 | 70.8 | Capped Score | 5 | source issue |
| Davante Adams | WR |  | LAR | 20 | 50.93 | 36 | 85.3 | Capped Score | 4 | source issue |
| Josh Allen | QB |  | BUF | 21 | 50.32 | 24 | 8.0 | Capped Score | 3 | source issue |
| Saquon Barkley | RB |  | PHI | 22 | 50.11 | 23 | 34.1 | Capped Score | 6 | source issue |
| Drake London | WR |  | ATL | 23 | 49.49 | 11 | 17.8 | Capped Score | 4 | source issue |
| Drake Maye | QB |  | NE | 24 | 49.35 | 27 | 15.8 | Scored + Warnings | 2 | needs human football review |
| Travis Kelce | TE |  | KC | 25 | 49.19 | 165 | 164.5 | Capped Score | 6 | source issue |

## Sentinel And Contamination Checks

| Player | Current NWR | Legacy Score | Lineage | Source Column | Status |
| --- | ---: | ---: | --- | --- | --- |
| Keenan Allen | 33.16 | 82.4 | review_v4_current_player | checkpoint_review_score | comparison-only legacy preserved |
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
