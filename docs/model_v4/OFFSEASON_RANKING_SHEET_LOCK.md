# Model v4 Offseason Ranking Sheet Lock

This is the canonical Model v4 source note for the league-rank roster file.

## Source Files

- Original PDF: `docs/model_v4/source_docs/LVE_Rosters_033126_3.pdf`
- Extracted text: `docs/model_v4/source_extracts/LVE_ROSTERS_033126_3.txt`
- Source title: `Las Vegas Enginerds 2026 Offseason Ranking List March 31, 2026`
- Ranking source shown in PDF extract: `FantasyPros February 27, 2026`
- Archived on: 2026-05-15

## Model v4 Treatment

- This file is rule-critical for roster declaration.
- League rank is a roster-rule signal, not model player quality.
- The `Roster's League-Rank Top Five` must be derived from this file or a
  verified structured import of this file.
- The required top-five release candidate pool is the roster's five highest
  league-ranked players only.
- This file should not directly tune Dynasty Asset Value.

## Niners Roster-Rank Lock

The extracted Niners roster column is:

| Roster Rank | Player | Pos | NFL Team | League Rank |
| ---: | --- | --- | --- | ---: |
| 1 | De'Von Achane | RB | MIA | 10 |
| 2 | Lamar Jackson | QB | BAL | 31 |
| 3 | Chase Brown | RB | CIN | 35 |
| 4 | Luther Burden | WR | CHI | 56 |
| 5 | Brian Thomas | WR | JAC | 66 |
| 6 | Ricky Pearsall | WR | SF | 91 |
| 7 | Quentin Johnston | WR | LAC | 94 |
| 8 | Jakobi Meyers | WR | JAC | 95 |
| 9 | David Montgomery | RB | HOU | 97 |
| 10 | Brandon Aiyuk | WR | SF | 98 |
| 11 | Oronde Gadsden | TE | LAC | 104 |
| 12 | Jake Ferguson | TE | DAL | 109 |
| 13 | Jayden Higgins | WR | HOU | 113 |
| 14 | Wan'Dale Robinson | WR | TEN | 118 |
| 15 | Brenton Strange | TE | JAC | 125 |
| 16 | Kaleb Johnson | RB | PIT | 131 |
| 17 | Xavier Worthy | WR | KC | 133 |
| 18 | Jalen Coker | WR | CAR | 147 |
| 19 | Jerry Jeudy | WR | CLE | 152 |
| 20 | Romeo Doubs | WR | NE | 172 |
| 21 | T.J. Hockenson | TE | MIN | 206 |
| 22 | Daniel Jones | QB | IND | 246 |
| 23 | Luke McCaffrey | WR | WAS | 263 |
| 24 | Devin Singletary | RB | NYG | 268 |

## Niners Required Top-Five Release Pool

These are the only players eligible for the required top-five release decision:

| Top-Five Slot | Player | Pos | NFL Team | League Rank |
| ---: | --- | --- | --- | ---: |
| 1 | De'Von Achane | RB | MIA | 10 |
| 2 | Lamar Jackson | QB | BAL | 31 |
| 3 | Chase Brown | RB | CIN | 35 |
| 4 | Luther Burden | WR | CHI | 56 |
| 5 | Brian Thomas | WR | JAC | 66 |

## Immediate v4 Implications

- Any forced-release UI that focuses first on non-top-five drops is wrong.
- Any model that labels Achane as a casual bubble/release player must fail a
  roster-decision sanity audit unless receipts clearly explain an extraordinary
  source-backed reason.
- The v4 roster decision layer must separately answer:
  - safest 23 keepers
  - required top-five release candidate
  - aggressive-smart trade/shop opportunities before June 15

## Open Parsing Work

- The PDF extraction is readable but multi-column and should be converted into a
  structured import before it drives production code.
- Sleeper remains the source of truth for traded pick ownership unless the user
  requests a PDF-vs-Sleeper pick audit.

