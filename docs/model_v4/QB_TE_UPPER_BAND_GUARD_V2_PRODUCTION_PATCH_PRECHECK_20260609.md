# QB/TE Upper-Band Guard v2 Production Patch Precheck - 2026-06-09

This precheck freezes the active Rankings baseline before the first production patch attempt for `qb_context_balance_te_upper_band_guard_v2`.

No production formula code had been edited when this snapshot was recorded.

## Hashes

- `full_player_board_value_review_rows.csv`: `cf32135966d397965e8a60cef2a8e4e243fe9d18cab5d8b439157f45af010dea`
- `current_player_value_full_board_review_rows.csv`: `41b2013e94e5386eebbc640cb1927721c3af5477c02399db6ed3aea8aae5660b`
- RB/WR row-level score checksum: `91e350a470d5f431bb304661e7053682c315a67ec25d9964a584bc4ac339a0b3`
- RB/WR scored rows: `172`

## Coverage

- Active rows: `240`
- QB/RB/WR/TE scored rows: `232`
- K rows: `8`
- No Private Score rows: `8`, all kickers
- Non-kicker source quarantine rows: `0`

## Top 25 Before

| Rank | Player | Pos | Team | Score | Trust |
|---:|---|---|---|---:|---|
| 1 | Trey McBride | TE | ARI | 87.4776 | Capped Score |
| 2 | Puka Nacua | WR | LAR | 83.0486 | Capped Score |
| 3 | Christian McCaffrey | RB | SF | 82.8329 | Capped Score |
| 4 | Jaxon Smith-Njigba | WR | SEA | 82.5714 | Capped Score |
| 5 | Josh Allen | QB | BUF | 80.3133 | Capped Score |
| 6 | Jonathan Taylor | RB | IND | 79.0510 | Capped Score |
| 7 | Bijan Robinson | RB | ATL | 78.4618 | Capped Score |
| 8 | Drake Maye | QB | NE | 77.0377 | Scored + Warnings |
| 9 | Trevor Lawrence | QB | JAX | 73.5624 | Scored |
| 10 | Jahmyr Gibbs | RB | DET | 70.7273 | Capped Score |
| 11 | Ja'Marr Chase | WR | CIN | 70.5399 | Capped Score |
| 12 | Amon-Ra St. Brown | WR | DET | 65.9348 | Capped Score |
| 13 | Derrick Henry | RB | BAL | 61.5505 | Capped Score |
| 14 | De'Von Achane | RB | MIA | 61.3322 | Capped Score |
| 15 | George Pickens | WR | DAL | 60.0258 | Capped Score |
| 16 | James Cook | RB | BUF | 59.6640 | Capped Score |
| 17 | Zay Flowers | WR | BAL | 56.5344 | Capped Score |
| 18 | Kyle Pitts | TE | ATL | 55.2691 | Capped Score |
| 19 | Matthew Stafford | QB | LAR | 55.0484 | Scored + Warnings |
| 20 | A.J. Brown | WR | PHI | 54.1764 | Capped Score |
| 21 | Chris Olave | WR | NO | 54.0656 | Capped Score |
| 22 | Kyren Williams | RB | LAR | 53.9777 | Capped Score |
| 23 | Nico Collins | WR | HOU | 53.4085 | Capped Score |
| 24 | Davante Adams | WR | LAR | 50.9317 | Capped Score |
| 25 | Travis Kelce | TE | KC | 50.9057 | Capped Score |

## Top 15 QBs Before

Josh Allen `#5`, Drake Maye `#8`, Trevor Lawrence `#9`, Matthew Stafford `#19`, Caleb Williams `#33`, Justin Herbert `#37`, Jalen Hurts `#42`, Bo Nix `#43`, Dak Prescott `#51`, Patrick Mahomes `#69`, Jared Goff `#83`, Baker Mayfield `#130`, Jaxson Dart `#147`, Lamar Jackson `#150`, Jordan Love `#153`.

## Top 15 TEs Before

Trey McBride `#1`, Kyle Pitts `#18`, Travis Kelce `#25`, Hunter Henry `#38`, Tyler Warren `#57`, Harold Fannin `#58`, Brock Bowers `#59`, Dalton Schultz `#64`, Jake Ferguson `#77`, George Kittle `#88`, Colston Loveland `#118`, Oronde Gadsden `#133`, Sam LaPorta `#149`, Dalton Kincaid `#152`, Cade Otton `#154`.

## My Team Before

Top My Team rows: De'Von Achane `#14`, Chase Brown `#28`, Wan'Dale Robinson `#52`, Jakobi Meyers `#75`, Jake Ferguson `#77`, Quentin Johnston `#78`, Jerry Jeudy `#80`, Brian Thomas `#90`, Brandon Aiyuk `#93`, Luther Burden `#94`.

## Sentinels Before

- Keenan Allen: current NWR score `33.1581`, legacy active-pack score `82.40`, lineage `review_v4_current_player`, source column `nwr_dynasty_score`.
- Darius Slayton: current NWR score `23.6148`, legacy active-pack score `78.88`, lineage `review_v4_current_player`, source column `nwr_dynasty_score`.

## Guardrail Freeze

- RotoWire remains source-repair/status/context only.
- Market and league ranks are display-only only.
- Outcome percentages remain blank/in development.
- Decision Board remains blocked.
