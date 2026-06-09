# QB/TE Upper-Band Guard v2 Production Patch Audit - 2026-06-09

This audit compares the patched active output to the frozen pre-patch baseline and the selected v2 shadow shape.

## Hashes
- full board before: `cf32135966d397965e8a60cef2a8e4e243fe9d18cab5d8b439157f45af010dea`
- full board after: `73786d1f58f1ff8071839883b34f48eae239ea17ff9d98960fd65efc2928e006`
- current-value before: `41b2013e94e5386eebbc640cb1927721c3af5477c02399db6ed3aea8aae5660b`
- current-value after: `a8d5bc681c1d782c532cf3d55b9b98127e94cc84e1b71a814db21be1e41eef1a`
- active output changed: True

## Acceptance Summary
- RB/WR score invariant: True
- sentinels safe: True
- contamination safe: True
- failed criteria: []
- verdict: `production_patch_ready_for_human_review`

## Top 25 Before Patch
| Rank | Player | Pos | Team | Score |
|---:|---|---|---|---:|
| 1 | Trey McBride | TE | ARI | 87.4776 |
| 2 | Puka Nacua | WR | LAR | 83.0486 |
| 3 | Christian McCaffrey | RB | SF | 82.8329 |
| 4 | Jaxon Smith-Njigba | WR | SEA | 82.5714 |
| 5 | Josh Allen | QB | BUF | 80.3133 |
| 6 | Jonathan Taylor | RB | IND | 79.051 |
| 7 | Bijan Robinson | RB | ATL | 78.4618 |
| 8 | Drake Maye | QB | NE | 77.0377 |
| 9 | Trevor Lawrence | QB | JAX | 73.5624 |
| 10 | Jahmyr Gibbs | RB | DET | 70.7273 |
| 11 | Ja'Marr Chase | WR | CIN | 70.5399 |
| 12 | Amon-Ra St. Brown | WR | DET | 65.9348 |
| 13 | Derrick Henry | RB | BAL | 61.5505 |
| 14 | De'Von Achane | RB | MIA | 61.3322 |
| 15 | George Pickens | WR | DAL | 60.0258 |
| 16 | James Cook | RB | BUF | 59.664 |
| 17 | Zay Flowers | WR | BAL | 56.5344 |
| 18 | Kyle Pitts | TE | ATL | 55.2691 |
| 19 | Matthew Stafford | QB | LAR | 55.0484 |
| 20 | A.J. Brown | WR | PHI | 54.1764 |
| 21 | Chris Olave | WR | NO | 54.0656 |
| 22 | Kyren Williams | RB | LAR | 53.9777 |
| 23 | Nico Collins | WR | HOU | 53.4085 |
| 24 | Davante Adams | WR | LAR | 50.9317 |
| 25 | Travis Kelce | TE | KC | 50.9057 |

## Top 25 After Patch
| Rank | Player | Pos | Team | Score | Delta |
|---:|---|---|---|---:|---:|
| 1 | Puka Nacua | WR | LAR | 83.0486 | -1 |
| 2 | Christian McCaffrey | RB | SF | 82.8329 | -1 |
| 3 | Jaxon Smith-Njigba | WR | SEA | 82.5714 | -1 |
| 4 | Jonathan Taylor | RB | IND | 79.051 | -2 |
| 5 | Bijan Robinson | RB | ATL | 78.4618 | -2 |
| 6 | Jahmyr Gibbs | RB | DET | 70.7273 | -4 |
| 7 | Ja'Marr Chase | WR | CIN | 70.5399 | -4 |
| 8 | Amon-Ra St. Brown | WR | DET | 65.9348 | -4 |
| 9 | Trey McBride | TE | ARI | 62.2578 | 8 |
| 10 | Derrick Henry | RB | BAL | 61.5505 | -3 |
| 11 | De'Von Achane | RB | MIA | 61.3322 | -3 |
| 12 | George Pickens | WR | DAL | 60.0258 | -3 |
| 13 | James Cook | RB | BUF | 59.664 | -3 |
| 14 | Zay Flowers | WR | BAL | 56.5344 | -3 |
| 15 | A.J. Brown | WR | PHI | 54.1764 | -5 |
| 16 | Chris Olave | WR | NO | 54.0656 | -5 |
| 17 | Kyren Williams | RB | LAR | 53.9777 | -5 |
| 18 | Nico Collins | WR | HOU | 53.4085 | -5 |
| 19 | Kyle Pitts | TE | ATL | 53.3402 | 1 |
| 20 | Davante Adams | WR | LAR | 50.9317 | -4 |
| 21 | Josh Allen | QB | BUF | 50.3163 | 16 |
| 22 | Saquon Barkley | RB | PHI | 50.1053 | -4 |
| 23 | Drake London | WR | ATL | 49.4925 | -4 |
| 24 | Drake Maye | QB | NE | 49.3504 | 16 |
| 25 | Travis Kelce | TE | KC | 49.1903 | 0 |

## Top 15 QBs Before Patch
| Rank | Player | Pos | Team | Score |
|---:|---|---|---|---:|
| 5 | Josh Allen | QB | BUF | 80.3133 |
| 8 | Drake Maye | QB | NE | 77.0377 |
| 9 | Trevor Lawrence | QB | JAX | 73.5624 |
| 19 | Matthew Stafford | QB | LAR | 55.0484 |
| 33 | Caleb Williams | QB | CHI | 47.1915 |
| 37 | Justin Herbert | QB | LAC | 43.9605 |
| 42 | Jalen Hurts | QB | PHI | 41.1499 |
| 43 | Bo Nix | QB | DEN | 40.4641 |
| 51 | Dak Prescott | QB | DAL | 36.7642 |
| 69 | Patrick Mahomes | QB | KC | 31.7813 |
| 83 | Jared Goff | QB | DET | 26.6217 |
| 130 | Baker Mayfield | QB | TB | 17.9197 |
| 147 | Jaxson Dart | QB | NYG | 15.708 |
| 150 | Lamar Jackson | QB | BAL | 15.2515 |
| 153 | Jordan Love | QB | GB | 15.0116 |

## Top 15 QBs After Patch
| Rank | Player | Pos | Team | Score | Delta |
|---:|---|---|---|---:|---:|
| 21 | Josh Allen | QB | BUF | 50.3163 | 16 |
| 24 | Drake Maye | QB | NE | 49.3504 | 16 |
| 31 | Trevor Lawrence | QB | JAX | 47.4404 | 22 |
| 45 | Matthew Stafford | QB | LAR | 37.1191 | 26 |
| 60 | Caleb Williams | QB | CHI | 32.9322 | 27 |
| 62 | Justin Herbert | QB | LAC | 31.157 | 25 |
| 69 | Bo Nix | QB | DEN | 29.2353 | 26 |
| 71 | Jalen Hurts | QB | PHI | 28.7722 | 29 |
| 77 | Dak Prescott | QB | DAL | 27.0641 | 26 |
| 89 | Patrick Mahomes | QB | KC | 24.1863 | 20 |
| 109 | Jared Goff | QB | DET | 21.4851 | 26 |
| 138 | Baker Mayfield | QB | TB | 16.561 | 8 |
| 147 | Jaxson Dart | QB | NYG | 15.6195 | 0 |
| 151 | Jordan Love | QB | GB | 15.0989 | -2 |
| 152 | Lamar Jackson | QB | BAL | 15.0935 | 2 |

## Top 15 TEs Before Patch
| Rank | Player | Pos | Team | Score |
|---:|---|---|---|---:|
| 1 | Trey McBride | TE | ARI | 87.4776 |
| 18 | Kyle Pitts | TE | ATL | 55.2691 |
| 25 | Travis Kelce | TE | KC | 50.9057 |
| 38 | Hunter Henry | TE | NE | 43.0176 |
| 57 | Tyler Warren | TE | IND | 35.5372 |
| 58 | Harold Fannin | TE | CLE | 35.367 |
| 59 | Brock Bowers | TE | LV | 34.9344 |
| 64 | Dalton Schultz | TE | HOU | 33.5524 |
| 77 | Jake Ferguson | TE | DAL | 27.6842 |
| 88 | George Kittle | TE | SF | 25.4179 |
| 118 | Colston Loveland | TE | CHI | 20.0592 |
| 133 | Oronde Gadsden | TE | LAC | 17.3397 |
| 149 | Sam LaPorta | TE | DET | 15.4274 |
| 152 | Dalton Kincaid | TE | BUF | 15.1153 |
| 154 | Cade Otton | TE | TB | 14.9381 |

## Top 15 TEs After Patch
| Rank | Player | Pos | Team | Score | Delta |
|---:|---|---|---|---:|---:|
| 9 | Trey McBride | TE | ARI | 62.2578 | 8 |
| 19 | Kyle Pitts | TE | ATL | 53.3402 | 1 |
| 25 | Travis Kelce | TE | KC | 49.1903 | 0 |
| 54 | Brock Bowers | TE | LV | 34.0184 | -5 |
| 57 | Hunter Henry | TE | NE | 33.3774 | 19 |
| 66 | Tyler Warren | TE | IND | 29.8687 | 9 |
| 67 | Harold Fannin | TE | CLE | 29.8635 | 9 |
| 72 | Dalton Schultz | TE | HOU | 28.4786 | 8 |
| 92 | Jake Ferguson | TE | DAL | 23.8928 | 15 |
| 104 | George Kittle | TE | SF | 22.3058 | 16 |
| 127 | Colston Loveland | TE | CHI | 18.5548 | 9 |
| 133 | Oronde Gadsden | TE | LAC | 17.1316 | 0 |
| 149 | Sam LaPorta | TE | DET | 15.3117 | 0 |
| 153 | Dalton Kincaid | TE | BUF | 15.0927 | 1 |
| 156 | Cade Otton | TE | TB | 14.7787 | 2 |

## Production vs Shadow
Production output is equivalent in broad shape to `qb_context_balance_te_upper_band_guard_v2`: no QB in the top 10, elite TE exceptions are present, Trey McBride is not #1, RB/WR scores are unchanged, and the selected movement pattern is close to shadow with small pipeline differences from lifecycle/checkpoint interactions.

## Decision Board
Decision Board remains blocked.
