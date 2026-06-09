# Rankings Post-Patch Acceptance Audit - 2026-06-09

## Executive Summary
Verdict: `rankings_accepted_for_human_review`.
The patched Rankings board is ready for human review and safe to use as the current Rankings baseline for review-only work if the UI smoke check remains clean.

## Acceptance Questions
- Ready for human review: yes.
- Safe current Rankings baseline: yes, for review-only use.
- Remaining source/identity blockers: 0 non-kicker blockers.
- Contamination risks: True.
- Remaining formula-shape concerns: yes, human-review watchlist remains for QB/TE/veteran/young-player shape, but no blocking acceptance failure.
- QB discipline: improved for 10-team 1QB; no QB is top 10.
- TE discipline: improved for no-TE-premium while allowing elite exceptions.
- RB/WR scores unchanged: True.
- My Team movement explainable: max absolute rank delta 15.
- Decision Board should remain blocked.
- Next page after Rankings acceptance: 2026 Draft Board / Rookie Draft page.

## Coverage Counts
| Metric | Count |
|---|---:|
| active_rows | 240 |
| qb_rb_wr_te_rows | 232 |
| kicker_rows | 8 |
| nwr_scored_rows | 232 |
| no_private_score_rows | 8 |
| source_quarantine_non_kickers | 0 |
| my_team_rows | 24 |

## Top 25
| Rank | Player | Pos | Team | Score |
|---:|---|---|---|---:|
| 1 | Puka Nacua | WR | LAR | 83.0486 |
| 2 | Christian McCaffrey | RB | SF | 82.8329 |
| 3 | Jaxon Smith-Njigba | WR | SEA | 82.5714 |
| 4 | Jonathan Taylor | RB | IND | 79.051 |
| 5 | Bijan Robinson | RB | ATL | 78.4618 |
| 6 | Jahmyr Gibbs | RB | DET | 70.7273 |
| 7 | Ja'Marr Chase | WR | CIN | 70.5399 |
| 8 | Amon-Ra St. Brown | WR | DET | 65.9348 |
| 9 | Trey McBride | TE | ARI | 62.2578 |
| 10 | Derrick Henry | RB | BAL | 61.5505 |
| 11 | De'Von Achane | RB | MIA | 61.3322 |
| 12 | George Pickens | WR | DAL | 60.0258 |
| 13 | James Cook | RB | BUF | 59.664 |
| 14 | Zay Flowers | WR | BAL | 56.5344 |
| 15 | A.J. Brown | WR | PHI | 54.1764 |
| 16 | Chris Olave | WR | NO | 54.0656 |
| 17 | Kyren Williams | RB | LAR | 53.9777 |
| 18 | Nico Collins | WR | HOU | 53.4085 |
| 19 | Kyle Pitts | TE | ATL | 53.3402 |
| 20 | Davante Adams | WR | LAR | 50.9317 |
| 21 | Josh Allen | QB | BUF | 50.3163 |
| 22 | Saquon Barkley | RB | PHI | 50.1053 |
| 23 | Drake London | WR | ATL | 49.4925 |
| 24 | Drake Maye | QB | NE | 49.3504 |
| 25 | Travis Kelce | TE | KC | 49.1903 |

## Top 15 QBs
| Rank | Player | Pos | Team | Score |
|---:|---|---|---|---:|
| 21 | Josh Allen | QB | BUF | 50.3163 |
| 24 | Drake Maye | QB | NE | 49.3504 |
| 31 | Trevor Lawrence | QB | JAX | 47.4404 |
| 45 | Matthew Stafford | QB | LAR | 37.1191 |
| 60 | Caleb Williams | QB | CHI | 32.9322 |
| 62 | Justin Herbert | QB | LAC | 31.157 |
| 69 | Bo Nix | QB | DEN | 29.2353 |
| 71 | Jalen Hurts | QB | PHI | 28.7722 |
| 77 | Dak Prescott | QB | DAL | 27.0641 |
| 89 | Patrick Mahomes | QB | KC | 24.1863 |
| 109 | Jared Goff | QB | DET | 21.4851 |
| 138 | Baker Mayfield | QB | TB | 16.561 |
| 147 | Jaxson Dart | QB | NYG | 15.6195 |
| 151 | Jordan Love | QB | GB | 15.0989 |
| 152 | Lamar Jackson | QB | BAL | 15.0935 |

## Top 15 TEs
| Rank | Player | Pos | Team | Score |
|---:|---|---|---|---:|
| 9 | Trey McBride | TE | ARI | 62.2578 |
| 19 | Kyle Pitts | TE | ATL | 53.3402 |
| 25 | Travis Kelce | TE | KC | 49.1903 |
| 54 | Brock Bowers | TE | LV | 34.0184 |
| 57 | Hunter Henry | TE | NE | 33.3774 |
| 66 | Tyler Warren | TE | IND | 29.8687 |
| 67 | Harold Fannin | TE | CLE | 29.8635 |
| 72 | Dalton Schultz | TE | HOU | 28.4786 |
| 92 | Jake Ferguson | TE | DAL | 23.8928 |
| 104 | George Kittle | TE | SF | 22.3058 |
| 127 | Colston Loveland | TE | CHI | 18.5548 |
| 133 | Oronde Gadsden | TE | LAC | 17.1316 |
| 149 | Sam LaPorta | TE | DET | 15.3117 |
| 153 | Dalton Kincaid | TE | BUF | 15.0927 |
| 156 | Cade Otton | TE | TB | 14.7787 |

## Remaining Suspicious Rows
| Player | Pos | Rank | Score | Trust | Issue |
|---|---|---:|---:|---|---|
| Trey McBride | TE | 9 | 62.2578 | Capped Score | te_no_premium_format_sanity |
| Kyle Pitts | TE | 19 | 53.3402 | Capped Score | te_no_premium_format_sanity |
| Travis Kelce | TE | 25 | 49.1903 | Capped Score | source_disclosure_gap |
| Brock Bowers | TE | 54 | 34.0184 | Capped Score | te_no_premium_format_sanity |
| Josh Allen | QB | 21 | 50.3163 | Capped Score | qb_1qb_format_sanity |
| Drake Maye | QB | 24 | 49.3504 | Scored + Warnings | qb_1qb_format_sanity |
| Patrick Mahomes | QB | 89 | 24.1863 | Scored + Warnings | qb_1qb_format_sanity |
| Lamar Jackson | QB | 152 | 15.0935 | Scored + Warnings | human_review_only |
| Joe Burrow | QB | 207 | 9.8866 | Capped Score | elite_player_too_low |
| Jayden Daniels | QB | 189 | 11.514 | Scored + Warnings | elite_player_too_low |
| Keenan Allen | WR | 58 | 33.1581 | Capped Score | still_human_review_needed |
| Darius Slayton | WR | 94 | 23.6148 | Capped Score | still_human_review_needed |
| De'Von Achane | RB | 11 | 61.3322 | Capped Score | still_human_review_needed |
| Chase Brown | RB | 26 | 49.1893 | Capped Score | still_human_review_needed |
| Brandon Aiyuk | WR | 90 | 24.1324 | Capped Score | still_human_review_needed |
| Jake Ferguson | TE | 92 | 23.8928 | Capped Score | te_no_premium_format_sanity |

## Guardrails
- Sentinels safe: True
- Contamination safe: True
- Market Rank and League Rank remain display-only.
- RotoWire remains source-repair/status/context only.
- Outcome percentages remain blank/in development.
- Kickers remain hidden/default-off.

## UI Smoke Check
Passed on `http://localhost:8501/` after restarting Streamlit with the patched Rankings page. The browser showed `Dynasty Rankings`, Active players shown 232, NWR scored 232, No private score 8, Puka Nacua as the selected Rank 1 detail row, display-only market/league language, legacy comparison-only disclosure, and outcome fields in development. No Decision Board recommendation language leaked into Rankings.
