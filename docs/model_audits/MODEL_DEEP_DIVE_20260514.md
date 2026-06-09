# Niners War Room Model Deep Dive - 2026-05-14

## Why This Audit Exists

The current question is not whether the UI is pretty. The current question is whether the rankings can be trusted. This report pulls the active stats-first preview outputs, normalized feature rows, contribution receipts, source coverage, outliers, lifecycle bridge metadata, and current Niners roster board into one place so weird rankings can be diagnosed from inputs and formulas instead of vibes.

**Bottom line:** the active board is better after the latest low-confidence safety patch, but it is still not clean enough to call final decision-ready. The most important remaining risks are independent projections, participation/route proxies, missing market references, and age/dropoff provenance. The model can be used as an audit board, not as final truth.

## Exported Ranking Files

- `C:\Dev\niners-war-room\local_exports\model_deep_dive_20260514\all_stats_first_preview_rankings.csv`
- `C:\Dev\niners-war-room\local_exports\model_deep_dive_20260514\visible_war_board_rankings.csv`
- `C:\Dev\niners-war-room\local_exports\model_deep_dive_20260514\niners_roster_rankings.csv`
- `C:\Dev\niners-war-room\local_exports\model_deep_dive_20260514\named_player_audit_table.csv`
- `C:\Dev\niners-war-room\local_exports\model_deep_dive_20260514\named_player_top_receipt_drivers.csv`
- `C:\Dev\niners-war-room\local_exports\model_deep_dive_20260514\suspicious_ranking_cases.csv`

The full active preview has **1,039 player rows**. The visible War Board has **232 rostered/league-context rows** after Sleeper/data-pack joins.

## Active Source Files

| file | rows | modified | path |
|---|---|---|---|
| model outputs | 1039 | 2026-05-14T00:16:28 | C:\Dev\niners-war-room\local_exports\active_veteran_model_public_sources\stats_first_veteran_model_preview_outputs.csv |
| normalized features | 1039 | 2026-05-14T00:15:54 | C:\Dev\niners-war-room\local_exports\active_veteran_model_public_sources\stats_first_normalized_features.csv |
| feature contributions | 25586 | 2026-05-14T00:16:28 | C:\Dev\niners-war-room\local_exports\active_veteran_model_public_sources\stats_first_feature_contributions.csv |
| outliers | 2479 | 2026-05-14T00:16:28 | C:\Dev\niners-war-room\local_exports\active_veteran_model_public_sources\stats_first_preview_outliers.csv |
| source coverage | 1039 | 2026-05-14T00:16:28 | C:\Dev\niners-war-room\local_exports\active_veteran_model_public_sources\stats_first_source_coverage.csv |


## How The Active Ranking Is Sorted

The generated preview writes `rank_audit` as `sort=keeper_score_desc|private_lve_value_desc`. That means the active ranking is not pure private football value. It is keeper-oriented: `keeper_score` first, then `private_lve_value`. If you want a pure talent/stat board, that sort policy itself may need to change or split into two boards.

## Position Summary

| position | players | top_50_count | avg_model_value | avg_confidence | top_player | top_player_rank |
|---|---|---|---|---|---|---|
| QB | 141 | 0 | 27.36 | 56.11 | Josh Allen | 230 |
| RB | 246 | 10 | 47.34 | 58.44 | Bijan Robinson | 9 |
| TE | 226 | 0 | 21.57 | 54.01 | Brock Bowers | 290 |
| WR | 426 | 40 | 39.87 | 54.72 | Justin Jefferson | 1 |


## Top 75 Overall Active Preview Rankings

| rk | posrk | player | pos | life | model | keeper | drop | conf | warn |
|---|---|---|---|---|---|---|---|---|---|
| 1 | WR1 | Justin Jefferson | WR | established_veteran | 79.5 | 77.62 | 20.83 | 77.5 | ready |
| 2 | WR2 | CeeDee Lamb | WR | established_veteran | 78.06 | 76.21 | 24.64 | 77.5 | model_warning |
| 3 | WR3 | Ja'Marr Chase | WR | established_veteran | 77.09 | 74.41 | 24.25 | 77.5 | model_warning |
| 4 | WR4 | Malik Nabers | WR | year_two_nfl_player | 77.37 | 74.16 | 24.78 | 75.5 | model_warning |
| 5 | WR5 | Amon-Ra St. Brown | WR | established_veteran | 76.61 | 73.98 | 25.34 | 77.5 | model_warning |
| 6 | WR6 | A.J. Brown | WR | established_veteran | 75.97 | 73.29 | 25.59 | 77.5 | model_warning |
| 7 | WR7 | Puka Nacua | WR | year_three_nfl_player | 75.37 | 73.04 | 25.83 | 75.5 | model_warning |
| 8 | WR8 | Brian Thomas Jr. | WR | year_two_nfl_player | 75.78 | 72.92 | 22.77 | 75.5 | ready |
| 9 | RB1 | Bijan Robinson | RB | year_three_nfl_player | 75.12 | 71.73 | 22.91 | 75.5 | ready |
| 10 | WR9 | Tyreek Hill | WR | established_veteran | 73.85 | 70.02 | 26.82 | 70.5 | model_warning |
| 11 | WR10 | Nico Collins | WR | established_veteran | 72.46 | 69.5 | 29.13 | 77.5 | model_warning |
| 12 | WR11 | DJ Moore | WR | established_veteran | 71.06 | 68.26 | 27.06 | 77.5 | ready |
| 13 | RB2 | Jahmyr Gibbs | RB | year_three_nfl_player | 70.73 | 67.59 | 30.0 | 75.5 | model_warning |
| 14 | WR12 | Davante Adams | WR | established_veteran | 70.58 | 67.38 | 29.73 | 77.5 | model_warning |
| 15 | WR13 | Stefon Diggs | WR | established_veteran | 70.19 | 67.25 | 25.95 | 77.5 | ready |
| 16 | WR14 | Garrett Wilson | WR | established_veteran | 69.61 | 67.04 | 33.33 | 77.5 | model_warning |
| 17 | WR15 | Drake London | WR | established_veteran | 69.14 | 66.52 | 34.33 | 77.5 | model_warning |
| 18 | WR16 | Mike Evans | WR | established_veteran | 69.62 | 66.48 | 34.45 | 77.5 | model_warning |
| 19 | WR17 | Keenan Allen | WR | established_veteran | 69.38 | 66.37 | 29.04 | 77.5 | model_warning |
| 20 | RB3 | Kenneth Walker III | RB | established_veteran | 68.54 | 66.34 | 28.15 | 77.5 | ready |
| 21 | WR18 | George Pickens | WR | established_veteran | 68.33 | 66.08 | 27.23 | 77.5 | ready |
| 22 | WR19 | Chris Godwin Jr. | WR | established_veteran | 68.24 | 65.76 | 28.66 | 77.5 | ready |
| 23 | WR20 | Marvin Harrison Jr. | WR | year_two_nfl_player | 68.97 | 65.73 | 32.37 | 75.5 | model_warning |
| 24 | WR21 | Ladd McConkey | WR | year_two_nfl_player | 68.28 | 65.39 | 31.5 | 75.5 | model_warning |
| 25 | WR22 | DeVonta Smith | WR | established_veteran | 67.78 | 65.38 | 33.15 | 77.5 | model_warning |
| 26 | WR23 | Tee Higgins | WR | established_veteran | 67.79 | 65.27 | 36.66 | 77.5 | model_warning |
| 27 | WR24 | Courtland Sutton | WR | established_veteran | 67.62 | 65.21 | 28.13 | 77.5 | ready |
| 28 | WR25 | Michael Pittman Jr. | WR | established_veteran | 67.59 | 65.15 | 30.0 | 77.5 | model_warning |
| 29 | WR26 | Brandon Aiyuk | WR | established_veteran | 67.2 | 64.83 | 28.57 | 77.5 | model_warning |
| 30 | WR27 | DK Metcalf | WR | established_veteran | 66.94 | 64.49 | 31.72 | 77.5 | model_warning |
| 31 | RB4 | James Cook | RB | established_veteran | 66.33 | 63.94 | 31.06 | 77.5 | ready |
| 32 | WR28 | Chris Olave | WR | established_veteran | 66.21 | 63.87 | 37.26 | 77.5 | model_warning |
| 33 | RB5 | Najee Harris | RB | established_veteran | 65.61 | 63.85 | 29.03 | 77.5 | model_warning |
| 34 | WR29 | Zay Flowers | WR | year_three_nfl_player | 66.23 | 63.72 | 32.24 | 75.5 | model_warning |
| 35 | WR30 | Terry McLaurin | WR | established_veteran | 66.03 | 63.56 | 36.32 | 77.5 | model_warning |
| 36 | RB6 | De'Von Achane | RB | year_three_nfl_player | 66.13 | 63.38 | 32.79 | 75.5 | model_warning |
| 37 | WR31 | Jakobi Meyers | WR | established_veteran | 65.5 | 63.2 | 33.78 | 77.5 | model_warning |
| 38 | WR32 | Amari Cooper | WR | established_veteran | 65.8 | 63.02 | 31.3 | 70.5 | data_warning |
| 39 | WR33 | Jerry Jeudy | WR | established_veteran | 64.33 | 62.38 | 32.39 | 77.5 | ready |
| 40 | WR34 | Calvin Ridley | WR | established_veteran | 64.45 | 62.13 | 35.43 | 77.5 | model_warning |
| 41 | WR35 | Cooper Kupp | WR | established_veteran | 64.45 | 62.1 | 31.76 | 77.5 | model_warning |
| 42 | WR36 | Hollywood Brown | WR | established_veteran | 63.82 | 61.34 | 35.85 | 70.5 | model_warning |
| 43 | WR37 | Jordan Addison | WR | year_three_nfl_player | 63.42 | 61.08 | 35.63 | 75.5 | model_warning |
| 44 | RB7 | Darrell Henderson | RB | established_veteran | 62.42 | 60.61 | 29.77 | 68.0 | model_warning |
| 45 | RB8 | Josh Jacobs | RB | established_veteran | 63.45 | 60.47 | 33.72 | 77.5 | model_warning |
| 46 | WR38 | Tank Dell | WR | year_three_nfl_player | 62.27 | 60.22 | 35.54 | 75.5 | model_warning |
| 47 | WR39 | Jaxon Smith-Njigba | WR | year_three_nfl_player | 62.29 | 60.18 | 33.66 | 75.5 | model_warning |
| 48 | RB9 | Kyren Williams | RB | established_veteran | 68.03 | 60.05 | 33.55 | 77.5 | model_warning |
| 49 | WR40 | Jaylen Waddle | WR | established_veteran | 61.78 | 59.93 | 37.87 | 77.5 | model_warning |
| 50 | RB10 | Zack Moss | RB | established_veteran | 61.95 | 59.87 | 33.02 | 72.5 | model_warning |
| 51 | RB11 | Saquon Barkley | RB | established_veteran | 67.98 | 59.84 | 31.22 | 77.5 | model_warning |
| 52 | RB12 | Sincere McCormick | RB | established_veteran | 60.54 | 59.56 | 33.78 | 68.0 | model_warning |
| 53 | WR41 | Nikko Remigio | WR | year_three_nfl_player | 60.99 | 59.18 | 37.41 | 70.5 | model_warning |
| 54 | WR42 | Darren Waller | WR | established_veteran | 61.14 | 59.09 | 35.41 | 77.5 | model_warning |
| 55 | WR43 | Diontae Johnson | WR | established_veteran | 61.24 | 59.03 | 36.48 | 70.5 | model_warning |
| 56 | RB13 | Travis Etienne | RB | established_veteran | 60.9 | 58.99 | 35.27 | 77.5 | model_warning |
| 57 | RB14 | Rachaad White | RB | established_veteran | 61.08 | 58.97 | 35.81 | 77.5 | model_warning |
| 58 | WR44 | Adam Thielen | WR | established_veteran | 60.56 | 57.87 | 37.1 | 70.5 | model_warning |
| 59 | RB15 | AJ Dillon | RB | established_veteran | 59.12 | 57.79 | 33.86 | 68.0 | model_warning |
| 60 | WR45 | DeAndre Hopkins | WR | established_veteran | 59.95 | 57.63 | 32.5 | 70.5 | model_warning |
| 61 | WR46 | Rashee Rice | WR | year_three_nfl_player | 60.63 | 57.58 | 38.82 | 75.5 | model_warning |
| 62 | RB16 | Christian McCaffrey | RB | established_veteran | 61.14 | 57.49 | 36.32 | 77.5 | model_warning |
| 63 | RB17 | RJ Harvey | RB | year_one_nfl_player | 61.89 | 56.97 | 41.26 | 38.5 | blocking |
| 64 | RB18 | Chuba Hubbard | RB | established_veteran | 59.25 | 56.94 | 37.7 | 77.5 | model_warning |
| 65 | RB19 | J.K. Dobbins | RB | established_veteran | 59.24 | 56.91 | 38.43 | 77.5 | model_warning |
| 66 | RB20 | TreVeyon Henderson | RB | year_one_nfl_player | 61.76 | 56.81 | 41.54 | 38.5 | blocking |
| 67 | RB21 | Jonathan Taylor | RB | established_veteran | 61.61 | 56.66 | 39.05 | 77.5 | model_warning |
| 68 | RB22 | La'Mical Perine | RB | established_veteran | 57.57 | 56.5 | 34.65 | 68.0 | model_warning |
| 69 | WR47 | Christian Kirk | WR | established_veteran | 58.13 | 56.47 | 41.42 | 77.5 | model_warning |
| 70 | RB23 | Quinshon Judkins | RB | year_one_nfl_player | 61.21 | 56.16 | 42.74 | 38.5 | blocking |
| 71 | RB24 | Derrick Henry | RB | established_veteran | 59.44 | 56.03 | 35.81 | 77.5 | model_warning |
| 72 | WR48 | Josh Downs | WR | year_three_nfl_player | 58.49 | 55.78 | 41.13 | 75.5 | model_warning |
| 73 | RB25 | Rico Dowdle | RB | established_veteran | 56.34 | 55.56 | 39.12 | 77.5 | model_warning |
| 74 | RB26 | Cam Akers | RB | established_veteran | 55.84 | 55.24 | 37.12 | 68.0 | model_warning |
| 75 | RB27 | Tyrone Tracy Jr. | RB | year_two_nfl_player | 55.71 | 55.02 | 40.13 | 75.5 | model_warning |


## Top 30 QB Rankings

| rk | posrk | player | life | model | keeper | drop | conf | warnings |
|---|---|---|---|---|---|---|---|---|
| 230 | QB1 | Josh Allen | established_veteran | 57.32 | 44.19 | 40.98 | 77.5 | model_warning |
| 236 | QB2 | Jalen Hurts | established_veteran | 56.65 | 43.65 | 45.42 | 77.5 | model_warning |
| 257 | QB3 | Bo Nix | year_two_nfl_player | 56.03 | 41.97 | 40.58 | 75.5 | model_warning |
| 261 | QB4 | Tyler Shough | year_one_nfl_player | 58.74 | 41.63 | 43.03 | 28.5 | blocking |
| 263 | QB5 | Lamar Jackson | established_veteran | 54.68 | 41.54 | 46.62 | 77.5 | model_warning |
| 317 | QB6 | Dillon Gabriel | year_one_nfl_player | 54.14 | 38.02 | 46.62 | 28.5 | blocking |
| 325 | QB7 | Caleb Williams | year_two_nfl_player | 51.52 | 37.38 | 43.52 | 73.0 | model_warning |
| 390 | QB8 | Brady Cook | year_one_nfl_player | 46.85 | 32.93 | 48.79 | 28.5 | blocking |
| 393 | QB9 | Jayden Daniels | year_two_nfl_player | 51.64 | 32.74 | 55.65 | 75.5 | model_warning |
| 396 | QB10 | Patrick Mahomes | established_veteran | 45.02 | 32.63 | 51.02 | 77.5 | model_warning |
| 407 | QB11 | Riley Leonard | year_one_nfl_player | 45.78 | 31.98 | 49.43 | 28.5 | blocking |
| 409 | QB12 | Justin Herbert | established_veteran | 44.17 | 31.86 | 50.79 | 77.5 | model_warning |
| 412 | QB13 | Baker Mayfield | established_veteran | 44.16 | 31.74 | 51.3 | 77.5 | model_warning |
| 415 | QB14 | Russell Wilson | established_veteran | 44.53 | 31.6 | 50.98 | 70.5 | model_warning |
| 421 | QB15 | Brock Purdy | established_veteran | 43.14 | 30.77 | 57.31 | 77.5 | model_warning |
| 423 | QB16 | Dak Prescott | established_veteran | 43.1 | 30.7 | 51.01 | 77.5 | model_warning |
| 439 | QB17 | Trevor Lawrence | established_veteran | 42.19 | 30.1 | 54.28 | 77.5 | model_warning |
| 450 | QB18 | C.J. Stroud | year_three_nfl_player | 42.66 | 29.77 | 55.08 | 75.5 | model_warning |
| 452 | QB19 | Bryce Young | year_three_nfl_player | 42.97 | 29.76 | 51.59 | 70.5 | model_warning |
| 457 | QB20 | Jared Goff | established_veteran | 41.86 | 29.61 | 49.89 | 77.5 | model_warning |
| 458 | QB21 | Quinn Ewers | year_one_nfl_player | 43.03 | 29.59 | 50.9 | 20.0 | blocking |
| 484 | QB22 | Sam Howell | established_veteran | 41.79 | 29.4 | 49.35 | 68.0 | model_warning |
| 499 | QB23 | Geno Smith | established_veteran | 41.75 | 28.89 | 51.14 | 70.5 | model_warning |
| 501 | QB24 | Jordan Love | established_veteran | 40.95 | 28.77 | 54.02 | 77.5 | model_warning |
| 527 | QB25 | Sam Darnold | established_veteran | 39.66 | 27.94 | 50.8 | 77.5 | model_warning |
| 553 | QB26 | Mac Jones | established_veteran | 39.01 | 27.01 | 50.69 | 68.0 | model_warning |
| 569 | QB27 | Cam Ward | year_one_nfl_player | 50.69 | 26.58 | 53.79 | 38.5 | blocking |
| 570 | QB28 | Tua Tagovailoa | established_veteran | 39.21 | 26.57 | 53.94 | 70.5 | model_warning |
| 579 | QB29 | Kirk Cousins | established_veteran | 38.59 | 26.21 | 51.87 | 70.5 | model_warning |
| 638 | QB30 | Deshaun Watson | established_veteran | 37.29 | 25.33 | 62.11 | 70.5 | model_warning |


## Top 30 RB Rankings

| rk | posrk | player | life | model | keeper | drop | conf | warnings |
|---|---|---|---|---|---|---|---|---|
| 9 | RB1 | Bijan Robinson | year_three_nfl_player | 75.12 | 71.73 | 22.91 | 75.5 | ready |
| 13 | RB2 | Jahmyr Gibbs | year_three_nfl_player | 70.73 | 67.59 | 30.0 | 75.5 | model_warning |
| 20 | RB3 | Kenneth Walker III | established_veteran | 68.54 | 66.34 | 28.15 | 77.5 | ready |
| 31 | RB4 | James Cook | established_veteran | 66.33 | 63.94 | 31.06 | 77.5 | ready |
| 33 | RB5 | Najee Harris | established_veteran | 65.61 | 63.85 | 29.03 | 77.5 | model_warning |
| 36 | RB6 | De'Von Achane | year_three_nfl_player | 66.13 | 63.38 | 32.79 | 75.5 | model_warning |
| 44 | RB7 | Darrell Henderson | established_veteran | 62.42 | 60.61 | 29.77 | 68.0 | model_warning |
| 45 | RB8 | Josh Jacobs | established_veteran | 63.45 | 60.47 | 33.72 | 77.5 | model_warning |
| 48 | RB9 | Kyren Williams | established_veteran | 68.03 | 60.05 | 33.55 | 77.5 | model_warning |
| 50 | RB10 | Zack Moss | established_veteran | 61.95 | 59.87 | 33.02 | 72.5 | model_warning |
| 51 | RB11 | Saquon Barkley | established_veteran | 67.98 | 59.84 | 31.22 | 77.5 | model_warning |
| 52 | RB12 | Sincere McCormick | established_veteran | 60.54 | 59.56 | 33.78 | 68.0 | model_warning |
| 56 | RB13 | Travis Etienne | established_veteran | 60.9 | 58.99 | 35.27 | 77.5 | model_warning |
| 57 | RB14 | Rachaad White | established_veteran | 61.08 | 58.97 | 35.81 | 77.5 | model_warning |
| 59 | RB15 | AJ Dillon | established_veteran | 59.12 | 57.79 | 33.86 | 68.0 | model_warning |
| 62 | RB16 | Christian McCaffrey | established_veteran | 61.14 | 57.49 | 36.32 | 77.5 | model_warning |
| 63 | RB17 | RJ Harvey | year_one_nfl_player | 61.89 | 56.97 | 41.26 | 38.5 | blocking |
| 64 | RB18 | Chuba Hubbard | established_veteran | 59.25 | 56.94 | 37.7 | 77.5 | model_warning |
| 65 | RB19 | J.K. Dobbins | established_veteran | 59.24 | 56.91 | 38.43 | 77.5 | model_warning |
| 66 | RB20 | TreVeyon Henderson | year_one_nfl_player | 61.76 | 56.81 | 41.54 | 38.5 | blocking |
| 67 | RB21 | Jonathan Taylor | established_veteran | 61.61 | 56.66 | 39.05 | 77.5 | model_warning |
| 68 | RB22 | La'Mical Perine | established_veteran | 57.57 | 56.5 | 34.65 | 68.0 | model_warning |
| 70 | RB23 | Quinshon Judkins | year_one_nfl_player | 61.21 | 56.16 | 42.74 | 38.5 | blocking |
| 71 | RB24 | Derrick Henry | established_veteran | 59.44 | 56.03 | 35.81 | 77.5 | model_warning |
| 73 | RB25 | Rico Dowdle | established_veteran | 56.34 | 55.56 | 39.12 | 77.5 | model_warning |
| 74 | RB26 | Cam Akers | established_veteran | 55.84 | 55.24 | 37.12 | 68.0 | model_warning |
| 75 | RB27 | Tyrone Tracy Jr. | year_two_nfl_player | 55.71 | 55.02 | 40.13 | 75.5 | model_warning |
| 76 | RB28 | Joe Mixon | established_veteran | 57.76 | 54.87 | 39.02 | 77.5 | model_warning |
| 77 | RB29 | Kevin Harris | established_veteran | 54.94 | 54.81 | 39.52 | 68.0 | model_warning |
| 78 | RB30 | Jordan Mason | established_veteran | 55.37 | 54.74 | 40.33 | 77.5 | model_warning |


## Top 30 WR Rankings

| rk | posrk | player | life | model | keeper | drop | conf | warnings |
|---|---|---|---|---|---|---|---|---|
| 1 | WR1 | Justin Jefferson | established_veteran | 79.5 | 77.62 | 20.83 | 77.5 | ready |
| 2 | WR2 | CeeDee Lamb | established_veteran | 78.06 | 76.21 | 24.64 | 77.5 | model_warning |
| 3 | WR3 | Ja'Marr Chase | established_veteran | 77.09 | 74.41 | 24.25 | 77.5 | model_warning |
| 4 | WR4 | Malik Nabers | year_two_nfl_player | 77.37 | 74.16 | 24.78 | 75.5 | model_warning |
| 5 | WR5 | Amon-Ra St. Brown | established_veteran | 76.61 | 73.98 | 25.34 | 77.5 | model_warning |
| 6 | WR6 | A.J. Brown | established_veteran | 75.97 | 73.29 | 25.59 | 77.5 | model_warning |
| 7 | WR7 | Puka Nacua | year_three_nfl_player | 75.37 | 73.04 | 25.83 | 75.5 | model_warning |
| 8 | WR8 | Brian Thomas Jr. | year_two_nfl_player | 75.78 | 72.92 | 22.77 | 75.5 | ready |
| 10 | WR9 | Tyreek Hill | established_veteran | 73.85 | 70.02 | 26.82 | 70.5 | model_warning |
| 11 | WR10 | Nico Collins | established_veteran | 72.46 | 69.5 | 29.13 | 77.5 | model_warning |
| 12 | WR11 | DJ Moore | established_veteran | 71.06 | 68.26 | 27.06 | 77.5 | ready |
| 14 | WR12 | Davante Adams | established_veteran | 70.58 | 67.38 | 29.73 | 77.5 | model_warning |
| 15 | WR13 | Stefon Diggs | established_veteran | 70.19 | 67.25 | 25.95 | 77.5 | ready |
| 16 | WR14 | Garrett Wilson | established_veteran | 69.61 | 67.04 | 33.33 | 77.5 | model_warning |
| 17 | WR15 | Drake London | established_veteran | 69.14 | 66.52 | 34.33 | 77.5 | model_warning |
| 18 | WR16 | Mike Evans | established_veteran | 69.62 | 66.48 | 34.45 | 77.5 | model_warning |
| 19 | WR17 | Keenan Allen | established_veteran | 69.38 | 66.37 | 29.04 | 77.5 | model_warning |
| 21 | WR18 | George Pickens | established_veteran | 68.33 | 66.08 | 27.23 | 77.5 | ready |
| 22 | WR19 | Chris Godwin Jr. | established_veteran | 68.24 | 65.76 | 28.66 | 77.5 | ready |
| 23 | WR20 | Marvin Harrison Jr. | year_two_nfl_player | 68.97 | 65.73 | 32.37 | 75.5 | model_warning |
| 24 | WR21 | Ladd McConkey | year_two_nfl_player | 68.28 | 65.39 | 31.5 | 75.5 | model_warning |
| 25 | WR22 | DeVonta Smith | established_veteran | 67.78 | 65.38 | 33.15 | 77.5 | model_warning |
| 26 | WR23 | Tee Higgins | established_veteran | 67.79 | 65.27 | 36.66 | 77.5 | model_warning |
| 27 | WR24 | Courtland Sutton | established_veteran | 67.62 | 65.21 | 28.13 | 77.5 | ready |
| 28 | WR25 | Michael Pittman Jr. | established_veteran | 67.59 | 65.15 | 30.0 | 77.5 | model_warning |
| 29 | WR26 | Brandon Aiyuk | established_veteran | 67.2 | 64.83 | 28.57 | 77.5 | model_warning |
| 30 | WR27 | DK Metcalf | established_veteran | 66.94 | 64.49 | 31.72 | 77.5 | model_warning |
| 32 | WR28 | Chris Olave | established_veteran | 66.21 | 63.87 | 37.26 | 77.5 | model_warning |
| 34 | WR29 | Zay Flowers | year_three_nfl_player | 66.23 | 63.72 | 32.24 | 75.5 | model_warning |
| 35 | WR30 | Terry McLaurin | established_veteran | 66.03 | 63.56 | 36.32 | 77.5 | model_warning |


## Top 30 TE Rankings

| rk | posrk | player | life | model | keeper | drop | conf | warnings |
|---|---|---|---|---|---|---|---|---|
| 290 | TE1 | Brock Bowers | year_two_nfl_player | 54.08 | 39.68 | 46.91 | 75.5 | model_warning |
| 343 | TE2 | Trey McBride | established_veteran | 48.37 | 35.82 | 47.24 | 77.5 | model_warning |
| 361 | TE3 | George Kittle | established_veteran | 47.91 | 35.07 | 51.6 | 77.5 | model_warning |
| 398 | TE4 | Sam LaPorta | year_three_nfl_player | 45.47 | 32.6 | 55.37 | 75.5 | model_warning |
| 405 | TE5 | Mark Andrews | established_veteran | 44.48 | 32.2 | 51.15 | 77.5 | model_warning |
| 411 | TE6 | Evan Engram | established_veteran | 43.93 | 31.77 | 49.8 | 77.5 | model_warning |
| 419 | TE7 | T.J. Hockenson | established_veteran | 43.46 | 31.11 | 57.57 | 77.5 | model_warning |
| 420 | TE8 | Jonnu Smith | established_veteran | 43.41 | 31.03 | 49.25 | 70.5 | model_warning |
| 436 | TE9 | Travis Kelce | established_veteran | 42.79 | 30.24 | 54.56 | 77.5 | model_warning |
| 500 | TE10 | David Njoku | established_veteran | 41.02 | 28.88 | 59.83 | 77.5 | model_warning |
| 505 | TE11 | Hunter Henry | established_veteran | 40.59 | 28.71 | 55.09 | 77.5 | model_warning |
| 511 | TE12 | Cole Kmet | established_veteran | 40.12 | 28.35 | 56.26 | 77.5 | model_warning |
| 530 | TE13 | Kyle Pitts | established_veteran | 39.43 | 27.84 | 55.49 | 77.5 | model_warning |
| 539 | TE14 | Dalton Kincaid | year_three_nfl_player | 39.96 | 27.56 | 59.91 | 75.5 | model_warning |
| 540 | TE15 | Zach Ertz | established_veteran | 39.35 | 27.48 | 53.89 | 77.5 | model_warning |
| 541 | TE16 | Dalton Schultz | established_veteran | 39.01 | 27.43 | 56.3 | 77.5 | model_warning |
| 556 | TE17 | Jake Ferguson | established_veteran | 38.34 | 26.8 | 56.86 | 77.5 | model_warning |
| 576 | TE18 | Pat Freiermuth | established_veteran | 37.82 | 26.37 | 57.04 | 77.5 | model_warning |
| 584 | TE19 | Cade Otton | established_veteran | 37.49 | 26.05 | 57.69 | 77.5 | model_warning |
| 588 | TE20 | Dallas Goedert | established_veteran | 38.18 | 25.94 | 61.94 | 70.5 | model_warning |
| 648 | TE21 | Tucker Kraft | year_three_nfl_player | 36.89 | 24.9 | 56.92 | 75.5 | model_warning |
| 654 | TE22 | Chig Okonkwo | established_veteran | 35.78 | 24.66 | 56.48 | 77.5 | model_warning |
| 673 | TE23 | Colston Loveland | year_one_nfl_player | 44.14 | 24.22 | 57.95 | 38.5 | blocking |
| 686 | TE24 | Juwan Johnson | established_veteran | 35.19 | 23.56 | 61.01 | 70.5 | model_warning |
| 697 | TE25 | Tyler Warren | year_one_nfl_player | 42.27 | 22.97 | 58.22 | 38.5 | blocking |
| 699 | TE26 | Tyler Conklin | established_veteran | 34.27 | 22.74 | 59.33 | 70.5 | model_warning |
| 701 | TE27 | Logan Thomas | established_veteran | 33.98 | 22.52 | 57.05 | 72.5 | model_warning |
| 710 | TE28 | Theo Johnson | year_two_nfl_player | 33.97 | 21.59 | 63.95 | 70.5 | model_warning |
| 717 | TE29 | Devin Culp | year_two_nfl_player | 32.66 | 21.04 | 58.81 | 70.5 | model_warning |
| 722 | TE30 | Isaiah Likely | established_veteran | 31.93 | 20.74 | 63.05 | 77.5 | model_warning |


## Niners Roster Board

This is the current My Team model surface after the low-confidence fix. Note that `Needs Data Review` is now a real section for young/no-NFL-evidence players rather than letting them hide as ordinary shop/cut candidates.

| section | player | pos | life | rank | action | model | keeper | cut | conf | top5 |
|---|---|---|---|---|---|---|---|---|---|---|
| Core Holds | Brian Thomas | WR | Young NFL Bridge | 66 | keep | 75.78 | 72.92 | 22.77 | 75.50 | Top-five protected slot |
| Forced-Release Decision | Luther Burden | WR | Young NFL Bridge | 56 | shop/release | 49.48 | 37.79 | 55.46 | 36.00 | Required top-five release slot |
| Needs Data Review | Oronde Gadsden | TE | Young NFL Bridge | 104 | review | 26.26 | 11.62 | 65.19 | 38.50 | Not in league-rank top five |
| Needs Data Review | Jayden Higgins | WR | Young NFL Bridge | 113 | review | 49.75 | 38.11 | 55.26 | 36.00 | Not in league-rank top five |
| Needs Data Review | Kaleb Johnson | RB | Young NFL Bridge | 131 | review | 53.16 | 48.20 | 51.88 | 36.00 | Not in league-rank top five |
| Bubble Players | Jakobi Meyers | WR | Established Veteran | 95 | bubble | 65.50 | 63.20 | 33.78 | 77.50 | Not in league-rank top five |
| Bubble Players | De'Von Achane | RB | Young NFL Bridge | 10 | bubble | 66.13 | 63.38 | 32.79 | 75.50 | Top-five protected slot |
| Bubble Players | Jerry Jeudy | WR | Established Veteran | 152 | bubble | 64.33 | 62.38 | 32.39 | 77.50 | Not in league-rank top five |
| Bubble Players | Brandon Aiyuk | WR | Established Veteran | 98 | bubble | 67.20 | 64.83 | 28.57 | 77.50 | Not in league-rank top five |
| Shop Candidates | Luke McCaffrey | WR | Young NFL Bridge | 263 | shop | 36.20 | 30.35 | 54.52 | 75.50 | Not in league-rank top five |
| Shop Candidates | Ricky Pearsall | WR | Young NFL Bridge | 91 | shop | 49.84 | 42.41 | 54.51 | 75.50 | Not in league-rank top five |
| Shop Candidates | Jalen Coker | WR | Young NFL Bridge | 147 | shop | 44.43 | 38.60 | 54.22 | 75.50 | Not in league-rank top five |
| Shop Candidates | Quentin Johnston | WR | Young NFL Bridge | 94 | shop | 50.49 | 43.97 | 48.23 | 75.50 | Not in league-rank top five |
| Shop Candidates | Lamar Jackson | QB | Established Veteran | 31 | shop | 54.68 | 41.54 | 46.62 | 77.50 | Top-five protected slot |
| Shop Candidates | David Montgomery | RB | Established Veteran | 97 | shop | 53.88 | 51.09 | 45.84 | 77.50 | Not in league-rank top five |
| Shop Candidates | Wan'Dale Robinson | WR | Established Veteran | 118 | shop | 55.43 | 53.21 | 45.58 | 77.50 | Not in league-rank top five |
| Shop Candidates | Romeo Doubs | WR | Established Veteran | 172 | shop | 55.17 | 48.81 | 43.30 | 77.50 | Not in league-rank top five |
| Shop Candidates | Chase Brown | RB | Young NFL Bridge | 35 | shop | 54.39 | 52.91 | 41.81 | 75.50 | Top-five protected slot |
| Shop Candidates | Xavier Worthy | WR | Young NFL Bridge | 133 | shop | 62.02 | 54.27 | 41.53 | 75.50 | Not in league-rank top five |
| Shop Candidates | Devin Singletary | RB | Established Veteran | 268 | shop | 53.47 | 52.76 | 40.85 | 77.50 | Not in league-rank top five |
| Bench/Stash | Brenton Strange | TE | Young NFL Bridge | 125 | drop | 27.51 | 16.11 | 66.12 | 75.50 | Not in league-rank top five |
| Bench/Stash | Daniel Jones | QB | Established Veteran | 246 | drop | 34.91 | 18.99 | 58.16 | 77.50 | Not in league-rank top five |
| Bench/Stash | T.J. Hockenson | TE | Established Veteran | 206 | drop | 43.46 | 31.11 | 57.57 | 77.50 | Not in league-rank top five |
| Bench/Stash | Jake Ferguson | TE | Established Veteran | 109 | drop | 38.34 | 26.80 | 56.86 | 77.50 | Not in league-rank top five |


## Named Player Audit

| overall_rank | position_rank | player_name | pos | lifecycle | model_value | keeper | drop | confidence | age_curve | recent_ppg | role | target | workload | bridge_weight | critical_missing | review_missing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 320 | WR99 | Luther Burden III | WR | year_one_nfl_player | 49.48 | 37.79 | 55.46 | 36.0 | 90.0 | 50.0 | 22.06 | 0.0 | 0.0 | 0.35 |  | projections/market/liquidity |
| 8 | WR8 | Brian Thomas Jr. | WR | year_two_nfl_player | 75.78 | 72.92 | 22.77 | 75.5 | 94.0 | 76.63 | 64.84 | 88.88 | 78.24 | 0.124 |  | independent projection/production freshness/market/liquidity |
| 36 | RB6 | De'Von Achane | RB | year_three_nfl_player | 66.13 | 63.38 | 32.79 | 75.5 | 95.0 | 85.36 | 65.26 | 75.93 | 62.49 | 0.047 |  | independent projection/production freshness/market/liquidity |
| 263 | QB5 | Lamar Jackson | QB | established_veteran | 54.68 | 41.54 | 46.62 | 77.5 | 92.0 | 89.92 | 75.24 | 50.0 | 0.96 | 0.0 |  | independent projection/production freshness/market/liquidity |
| 93 | RB41 | Chase Brown | RB | year_three_nfl_player | 54.39 | 52.91 | 41.81 | 75.5 | 82.0 | 59.45 | 58.06 | 52.28 | 54.72 | 0.047 |  | independent projection/production freshness/market/liquidity |
| 137 | RB83 | Kaleb Johnson | RB | year_one_nfl_player | 53.16 | 48.2 | 51.88 | 36.0 | 95.0 | 50.0 | 10.53 | 0.0 | 0.03 | 0.35 |  | projections/market/liquidity |
| 316 | WR98 | Jayden Higgins | WR | year_one_nfl_player | 49.75 | 38.11 | 55.26 | 36.0 | 94.0 | 50.0 | 22.09 | 0.0 | 0.0 | 0.35 |  | projections/market/liquidity |
| 759 | TE39 | Brenton Strange | TE | year_three_nfl_player | 27.51 | 16.11 | 66.12 | 75.5 | 92.0 | 30.53 | 39.38 | 47.18 | 32.63 | 0.047 |  | independent projection/production freshness/market/liquidity |
| 47 | WR39 | Jaxon Smith-Njigba | WR | year_three_nfl_player | 62.29 | 60.18 | 33.66 | 75.5 | 94.0 | 49.76 | 59.43 | 70.25 | 67.65 | 0.047 |  | independent projection/production freshness/market/liquidity |
| 26 | WR23 | Tee Higgins | WR | established_veteran | 67.79 | 65.27 | 36.66 | 77.5 | 94.0 | 68.64 | 59.42 | 82.23 | 77.08 | 0.0 |  | independent projection/production freshness/market/liquidity |
| 9 | RB1 | Bijan Robinson | RB | year_three_nfl_player | 75.12 | 71.73 | 22.91 | 75.5 | 95.0 | 90.33 | 71.53 | 82.05 | 80.25 | 0.047 |  | independent projection/production freshness/market/liquidity |
| 13 | RB2 | Jahmyr Gibbs | RB | year_three_nfl_player | 70.73 | 67.59 | 30.0 | 75.5 | 95.0 | 96.84 | 48.29 | 71.68 | 71.41 | 0.047 |  | independent projection/production freshness/market/liquidity |
| 48 | RB9 | Kyren Williams | RB | established_veteran | 68.03 | 60.05 | 33.55 | 77.5 | 95.0 | 100.0 | 70.54 | 56.21 | 89.85 | 0.0 |  | independent projection/production freshness/market/liquidity |
| 32 | WR28 | Chris Olave | WR | established_veteran | 66.21 | 63.87 | 37.26 | 77.5 | 94.0 | 57.5 | 63.5 | 83.54 | 75.83 | 0.0 |  | independent projection/production freshness/market/liquidity |
| 76 | RB28 | Joe Mixon | RB | established_veteran | 57.76 | 54.87 | 39.02 | 77.5 | 58.0 | 85.54 | 61.73 | 64.21 | 79.91 | 0.0 |  | independent projection/production freshness/market/liquidity |
| 31 | RB4 | James Cook | RB | established_veteran | 66.33 | 63.94 | 31.06 | 77.5 | 82.0 | 81.02 | 62.22 | 50.86 | 64.95 | 0.0 |  | independent projection/production freshness/market/liquidity |
| 62 | RB16 | Christian McCaffrey | RB | established_veteran | 61.14 | 57.49 | 36.32 | 77.5 | 58.0 | 100.0 | 73.93 | 87.12 | 85.66 | 0.0 |  | independent projection/production freshness/market/liquidity |


## Named Player Receipt Drivers

These are the largest component contributions for the named players. Positive contribution does not mean 'good input' by itself; it means this feature materially moved one of the model components.

| player_name | component | feature | score | weight | contribution |
|---|---|---|---|---|---|
| Luther Burden III | private_lve_value | young_nfl_bridge_prior | 82.00 | 35.00 | 17.51 |
| Luther Burden III | private_lve_value | dynasty_hold_value | 29.80 | 58.00 | 17.28 |
| Luther Burden III | dynasty_hold_value | age_curve | 90.00 | 18.00 | 16.20 |
| Luther Burden III | private_lve_value | win_now_value | 34.97 | 42.00 | 14.69 |
| Luther Burden III | dynasty_hold_value | lve_structural_formula_adjustment | -14.00 | 0.00 | -14.00 |
| Luther Burden III | dynasty_hold_value | route_role | 50.00 | 18.00 | 9.00 |
| Luther Burden III | win_now_value | route_role | 50.00 | 14.00 | 7.00 |
| Luther Burden III | win_now_value | weighted_recent_lve_ppg_score | 50.00 | 14.00 | 7.00 |
| Luther Burden III | dynasty_hold_value | production_stability | 50.00 | 14.00 | 7.00 |
| Luther Burden III | win_now_value | expected_lve_points_score | 50.00 | 12.00 | 6.00 |
| Brian Thomas Jr. | private_lve_value | dynasty_hold_value | 76.86 | 58.00 | 44.58 |
| Brian Thomas Jr. | private_lve_value | win_now_value | 69.51 | 42.00 | 29.19 |
| Brian Thomas Jr. | dynasty_hold_value | target_earning_stability | 88.88 | 24.00 | 21.33 |
| Brian Thomas Jr. | win_now_value | target_earning_stability | 88.88 | 20.00 | 17.78 |
| Brian Thomas Jr. | dynasty_hold_value | age_curve | 94.00 | 18.00 | 16.92 |
| Brian Thomas Jr. | dynasty_hold_value | route_role | 76.85 | 18.00 | 13.83 |
| Brian Thomas Jr. | win_now_value | role_security | 64.84 | 18.00 | 11.67 |
| Brian Thomas Jr. | win_now_value | route_role | 76.85 | 14.00 | 10.76 |
| Brian Thomas Jr. | win_now_value | weighted_recent_lve_ppg_score | 76.63 | 14.00 | 10.73 |
| Brian Thomas Jr. | dynasty_hold_value | production_stability | 63.85 | 14.00 | 8.94 |
| De'Von Achane | private_lve_value | dynasty_hold_value | 66.63 | 60.00 | 39.98 |
| De'Von Achane | private_lve_value | win_now_value | 64.53 | 40.00 | 25.81 |
| De'Von Achane | dynasty_hold_value | age_curve | 95.00 | 24.00 | 22.80 |
| De'Von Achane | win_now_value | weighted_recent_lve_ppg_score | 85.36 | 18.00 | 15.36 |
| De'Von Achane | win_now_value | lve_projection_value | 62.37 | 18.00 | 11.23 |
| De'Von Achane | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| De'Von Achane | dynasty_hold_value | injury_durability | 59.18 | 18.00 | 10.65 |
| De'Von Achane | dynasty_hold_value | workload_earning | 62.49 | 16.00 | 10.00 |
| De'Von Achane | win_now_value | role_security | 65.26 | 14.00 | 9.14 |
| De'Von Achane | win_now_value | workload_earning | 62.49 | 12.00 | 7.50 |
| Lamar Jackson | private_lve_value | dynasty_hold_value | 62.77 | 56.00 | 35.15 |
| Lamar Jackson | private_lve_value | win_now_value | 67.10 | 44.00 | 29.52 |
| Lamar Jackson | win_now_value | role_security | 75.24 | 28.00 | 21.07 |
| Lamar Jackson | dynasty_hold_value | role_security | 75.24 | 24.00 | 18.06 |
| Lamar Jackson | win_now_value | weighted_recent_lve_ppg_score | 89.92 | 16.00 | 14.39 |
| Lamar Jackson | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Lamar Jackson | dynasty_hold_value | start_gated_rushing_profile | 46.29 | 22.00 | 10.18 |
| Lamar Jackson | private_lve_value | qb_replacement_suppression | -10.00 | 0.00 | -10.00 |
| Lamar Jackson | dynasty_hold_value | age_curve | 92.00 | 10.00 | 9.20 |
| Lamar Jackson | dynasty_hold_value | efficiency_score | 89.92 | 10.00 | 8.99 |
| Chase Brown | private_lve_value | dynasty_hold_value | 55.44 | 60.00 | 33.26 |
| Chase Brown | private_lve_value | win_now_value | 54.10 | 40.00 | 21.64 |
| Chase Brown | dynasty_hold_value | age_curve | 82.00 | 24.00 | 19.68 |
| Chase Brown | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Chase Brown | win_now_value | weighted_recent_lve_ppg_score | 59.45 | 18.00 | 10.70 |
| Chase Brown | win_now_value | lve_projection_value | 53.31 | 18.00 | 9.60 |
| Chase Brown | dynasty_hold_value | injury_durability | 50.36 | 18.00 | 9.06 |
| Chase Brown | dynasty_hold_value | workload_earning | 54.72 | 16.00 | 8.76 |
| Chase Brown | win_now_value | role_security | 58.06 | 14.00 | 8.13 |
| Chase Brown | win_now_value | workload_earning | 54.72 | 12.00 | 6.57 |
| Kaleb Johnson | private_lve_value | dynasty_hold_value | 45.15 | 60.00 | 27.09 |
| Kaleb Johnson | dynasty_hold_value | age_curve | 95.00 | 24.00 | 22.80 |
| Kaleb Johnson | private_lve_value | win_now_value | 38.48 | 40.00 | 15.39 |
| Kaleb Johnson | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Kaleb Johnson | private_lve_value | young_nfl_bridge_prior | 73.00 | 35.00 | 10.68 |
| Kaleb Johnson | win_now_value | weighted_recent_lve_ppg_score | 50.00 | 18.00 | 9.00 |
| Kaleb Johnson | win_now_value | lve_projection_value | 50.00 | 18.00 | 9.00 |
| Kaleb Johnson | dynasty_hold_value | injury_durability | 50.00 | 18.00 | 9.00 |
| Kaleb Johnson | dynasty_hold_value | expected_lve_points_score | 50.00 | 12.00 | 6.00 |
| Kaleb Johnson | win_now_value | first_down_td_fit_capped | 50.00 | 10.00 | 5.00 |
| Jayden Higgins | private_lve_value | dynasty_hold_value | 30.52 | 58.00 | 17.70 |
| Jayden Higgins | private_lve_value | young_nfl_bridge_prior | 82.00 | 35.00 | 17.36 |
| Jayden Higgins | dynasty_hold_value | age_curve | 94.00 | 18.00 | 16.92 |
| Jayden Higgins | private_lve_value | win_now_value | 34.98 | 42.00 | 14.69 |
| Jayden Higgins | dynasty_hold_value | lve_structural_formula_adjustment | -14.00 | 0.00 | -14.00 |
| Jayden Higgins | dynasty_hold_value | route_role | 50.00 | 18.00 | 9.00 |
| Jayden Higgins | win_now_value | route_role | 50.00 | 14.00 | 7.00 |
| Jayden Higgins | win_now_value | weighted_recent_lve_ppg_score | 50.00 | 14.00 | 7.00 |
| Jayden Higgins | dynasty_hold_value | production_stability | 50.00 | 14.00 | 7.00 |
| Jayden Higgins | win_now_value | expected_lve_points_score | 50.00 | 12.00 | 6.00 |
| Brenton Strange | private_lve_value | dynasty_hold_value | 41.84 | 60.00 | 25.10 |
| Brenton Strange | private_lve_value | te_no_premium_suppression | -18.00 | 0.00 | -18.00 |
| Brenton Strange | private_lve_value | win_now_value | 44.91 | 40.00 | 17.96 |
| Brenton Strange | dynasty_hold_value | route_role | 50.00 | 30.00 | 15.00 |
| Brenton Strange | win_now_value | route_role | 50.00 | 28.00 | 14.00 |
| Brenton Strange | dynasty_hold_value | target_earning_stability | 47.18 | 24.00 | 11.32 |
| Brenton Strange | dynasty_hold_value | age_curve | 92.00 | 12.00 | 11.04 |
| Brenton Strange | win_now_value | target_earning_stability | 47.18 | 22.00 | 10.38 |
| Brenton Strange | dynasty_hold_value | lve_structural_formula_adjustment | -9.05 | 0.00 | -9.05 |
| Brenton Strange | win_now_value | expected_lve_points_score | 50.00 | 16.00 | 8.00 |
| Jaxon Smith-Njigba | private_lve_value | dynasty_hold_value | 64.21 | 58.00 | 37.24 |
| Jaxon Smith-Njigba | private_lve_value | win_now_value | 56.37 | 42.00 | 23.68 |
| Jaxon Smith-Njigba | dynasty_hold_value | age_curve | 94.00 | 18.00 | 16.92 |
| Jaxon Smith-Njigba | dynasty_hold_value | target_earning_stability | 70.25 | 24.00 | 16.86 |
| Jaxon Smith-Njigba | win_now_value | target_earning_stability | 70.25 | 20.00 | 14.05 |
| Jaxon Smith-Njigba | dynasty_hold_value | route_role | 63.25 | 18.00 | 11.38 |
| Jaxon Smith-Njigba | win_now_value | role_security | 59.43 | 18.00 | 10.70 |
| Jaxon Smith-Njigba | win_now_value | route_role | 63.25 | 14.00 | 8.86 |
| Jaxon Smith-Njigba | dynasty_hold_value | production_stability | 49.88 | 14.00 | 6.98 |
| Jaxon Smith-Njigba | win_now_value | weighted_recent_lve_ppg_score | 49.76 | 14.00 | 6.97 |
| Tee Higgins | private_lve_value | dynasty_hold_value | 69.90 | 58.00 | 40.54 |
| Tee Higgins | private_lve_value | win_now_value | 64.88 | 42.00 | 27.25 |
| Tee Higgins | dynasty_hold_value | target_earning_stability | 82.23 | 24.00 | 19.74 |
| Tee Higgins | dynasty_hold_value | age_curve | 94.00 | 18.00 | 16.92 |
| Tee Higgins | win_now_value | target_earning_stability | 82.23 | 20.00 | 16.45 |
| Tee Higgins | dynasty_hold_value | route_role | 72.14 | 18.00 | 12.99 |
| Tee Higgins | win_now_value | role_security | 59.42 | 18.00 | 10.70 |
| Tee Higgins | win_now_value | route_role | 72.14 | 14.00 | 10.10 |
| Tee Higgins | win_now_value | weighted_recent_lve_ppg_score | 68.64 | 14.00 | 9.61 |
| Tee Higgins | dynasty_hold_value | production_stability | 59.69 | 14.00 | 8.36 |
| Bijan Robinson | private_lve_value | dynasty_hold_value | 77.05 | 60.00 | 46.23 |
| Bijan Robinson | private_lve_value | win_now_value | 69.53 | 40.00 | 27.81 |
| Bijan Robinson | dynasty_hold_value | age_curve | 95.00 | 24.00 | 22.80 |
| Bijan Robinson | win_now_value | weighted_recent_lve_ppg_score | 90.33 | 18.00 | 16.26 |
| Bijan Robinson | dynasty_hold_value | injury_durability | 86.36 | 18.00 | 15.54 |
| Bijan Robinson | dynasty_hold_value | workload_earning | 80.25 | 16.00 | 12.84 |
| Bijan Robinson | win_now_value | lve_projection_value | 64.12 | 18.00 | 11.54 |
| Bijan Robinson | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Bijan Robinson | win_now_value | role_security | 71.53 | 14.00 | 10.01 |
| Bijan Robinson | win_now_value | workload_earning | 80.25 | 12.00 | 9.63 |
| Jahmyr Gibbs | private_lve_value | dynasty_hold_value | 71.59 | 60.00 | 42.95 |
| Jahmyr Gibbs | private_lve_value | win_now_value | 66.94 | 40.00 | 26.78 |
| Jahmyr Gibbs | dynasty_hold_value | age_curve | 95.00 | 24.00 | 22.80 |
| Jahmyr Gibbs | win_now_value | weighted_recent_lve_ppg_score | 96.84 | 18.00 | 17.43 |
| Jahmyr Gibbs | dynasty_hold_value | injury_durability | 69.04 | 18.00 | 12.43 |
| Jahmyr Gibbs | win_now_value | lve_projection_value | 66.39 | 18.00 | 11.95 |
| Jahmyr Gibbs | dynasty_hold_value | workload_earning | 71.41 | 16.00 | 11.43 |
| Jahmyr Gibbs | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Jahmyr Gibbs | win_now_value | workload_earning | 71.41 | 12.00 | 8.57 |
| Jahmyr Gibbs | win_now_value | first_down_td_fit_capped | 70.00 | 10.00 | 7.00 |
| Kyren Williams | private_lve_value | dynasty_hold_value | 64.99 | 60.00 | 38.99 |
| Kyren Williams | private_lve_value | win_now_value | 72.59 | 40.00 | 29.04 |
| Kyren Williams | dynasty_hold_value | age_curve | 95.00 | 24.00 | 22.80 |
| Kyren Williams | win_now_value | weighted_recent_lve_ppg_score | 100.00 | 18.00 | 18.00 |
| Kyren Williams | dynasty_hold_value | workload_earning | 89.85 | 16.00 | 14.38 |
| Kyren Williams | win_now_value | lve_projection_value | 67.50 | 18.00 | 12.15 |
| Kyren Williams | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Kyren Williams | win_now_value | workload_earning | 89.85 | 12.00 | 10.78 |
| Kyren Williams | win_now_value | role_security | 70.54 | 14.00 | 9.88 |
| Kyren Williams | dynasty_hold_value | injury_durability | 43.22 | 18.00 | 7.78 |
| Chris Olave | private_lve_value | dynasty_hold_value | 68.49 | 58.00 | 39.72 |
| Chris Olave | private_lve_value | win_now_value | 63.07 | 42.00 | 26.49 |
| Chris Olave | dynasty_hold_value | target_earning_stability | 83.54 | 24.00 | 20.05 |
| Chris Olave | dynasty_hold_value | age_curve | 94.00 | 18.00 | 16.92 |
| Chris Olave | win_now_value | target_earning_stability | 83.54 | 20.00 | 16.71 |
| Chris Olave | dynasty_hold_value | route_role | 71.76 | 18.00 | 12.92 |
| Chris Olave | win_now_value | role_security | 63.50 | 18.00 | 11.43 |
| Chris Olave | win_now_value | route_role | 71.76 | 14.00 | 10.05 |
| Chris Olave | win_now_value | weighted_recent_lve_ppg_score | 57.50 | 14.00 | 8.05 |
| Chris Olave | dynasty_hold_value | production_stability | 53.90 | 14.00 | 7.55 |
| Joe Mixon | private_lve_value | dynasty_hold_value | 52.26 | 60.00 | 31.36 |
| Joe Mixon | private_lve_value | win_now_value | 66.01 | 40.00 | 26.40 |
| Joe Mixon | win_now_value | weighted_recent_lve_ppg_score | 85.54 | 18.00 | 15.40 |
| Joe Mixon | dynasty_hold_value | age_curve | 58.00 | 24.00 | 13.92 |
| Joe Mixon | dynasty_hold_value | workload_earning | 79.91 | 16.00 | 12.79 |
| Joe Mixon | win_now_value | lve_projection_value | 62.44 | 18.00 | 11.24 |
| Joe Mixon | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| Joe Mixon | win_now_value | workload_earning | 79.91 | 12.00 | 9.59 |
| Joe Mixon | win_now_value | role_security | 61.73 | 14.00 | 8.64 |
| Joe Mixon | dynasty_hold_value | injury_durability | 44.70 | 18.00 | 8.05 |
| James Cook | private_lve_value | dynasty_hold_value | 68.39 | 60.00 | 41.03 |
| James Cook | private_lve_value | win_now_value | 63.24 | 40.00 | 25.30 |
| James Cook | dynasty_hold_value | age_curve | 82.00 | 24.00 | 19.68 |
| James Cook | win_now_value | weighted_recent_lve_ppg_score | 81.02 | 18.00 | 14.58 |
| James Cook | dynasty_hold_value | injury_durability | 74.72 | 18.00 | 13.45 |
| James Cook | win_now_value | expected_lve_points_score | 50.00 | 22.00 | 11.00 |
| James Cook | win_now_value | lve_projection_value | 60.86 | 18.00 | 10.95 |
| James Cook | dynasty_hold_value | workload_earning | 64.95 | 16.00 | 10.39 |
| James Cook | win_now_value | role_security | 62.22 | 14.00 | 8.71 |
| James Cook | win_now_value | workload_earning | 64.95 | 12.00 | 7.79 |


## Formula Map

Source references:
- `src/services/lve_stats_first_veteran_formula_service.py`: core scoring functions.
- `src/services/young_nfl_bridge_service.py`: first-three-year rookie/draft-capital bridge.
- `src/services/lve_normalization_service.py`: raw imported stats to normalized 0-100 features.
- `scripts/generate_stats_first_model_preview.py`: age-curve overlay, source coverage, outlier generation, and active preview generation.

### Private Value Components

- QB: win-now and dynasty hold are blended, then suppressed toward replacement unless the QB clears an elite exception. This is the 1QB/3-point-passing-TD suppression layer.
- RB: `private_lve_value = 0.40 * win_now + 0.60 * dynasty_hold`, with a cap if dynasty hold is weak. RB dynasty hold heavily weights age and injury, but the active ranking can still look RB-heavy when the imported role/production data is stronger than WR data.
- WR: `private_lve_value = 0.42 * win_now + 0.58 * dynasty_hold`, with target earning, route role, age, and production stability leading the hold score.
- TE: route role and target earning are mandatory; non-elite TEs are suppressed because there is no TE premium.

### Keeper, Trade, Drop, Confidence

- Keeper: `0.72 * private_lve_value + 0.18 * horizon_retention + 0.05 * confidence + structural_adjustment + lineup_adjustment`. Market is explicitly ignored.
- Trade: `0.42 * market_liquidity + 0.30 * private_lve_value + 0.18 * keeper_score + 0.10 * confidence + liquidity_adjustment`. This is the one major score where market matters.
- Drop: `0.48 * (100 - keeper) + 0.17 * (100 - private) + 0.15 * role_risk + 0.10 * health_risk`. This is football cut risk, not forced-release rule pain.
- Confidence: starts from normalized source confidence, subtracts half of missing-data penalty, then subtracts up to 8 points for warnings.

## Normalized Feature Buckets

The normalized feature rows currently include: `weighted_recent_lve_ppg_score`, `expected_lve_points_score`, `lve_projection_value`, `role_security`, `workload_earning`, `target_earning_stability`, `route_role`, `efficiency_score`, `first_down_td_fit`, `age_curve`, `injury_durability`, `private_stat_value`, `confidence`, and `missing_data_penalty`.

Critical model caveat: `expected_lve_points_score` is often neutral 50 because the generated projection file is a local baseline from recent LVE scoring, not an independent projection source. That avoids fake certainty, but it also means the board is not yet using true forward-looking projections.

## Young NFL Bridge

The bridge exists because year-one/year-two/year-three players should not be evaluated as pure veterans or pure rookies. Its current weights are:
| bucket | base_weight | meaning |
|---|---|---|
| incoming / true rookie | 100% | rookie/prospect context dominates |
| after rookie season | 35% before evidence decay | draft/prospect prior still meaningful |
| after second season | 20% before evidence decay | NFL evidence mostly takes over |
| after third season | 8% before evidence decay | small prior only |
| year four plus | 0% | draft capital becomes display-only |

The bridge decays faster when NFL evidence is present. Evidence is counted from recent LVE scoring, expected/projection fields, role/security, and source confidence. This is why low-confidence young players can still be unstable: missing NFL data can preserve prior weight, while poor role data can also drag them down.

## Age Dropoff Bridge Finding

Age is currently present in active normalized rows, but the implementation path is split: `lve_normalization_service.py` initially emits neutral age 50 and age receipts saying the source is not imported; then `scripts/generate_stats_first_model_preview.py` overlays age from Sleeper/nflverse bio and recalculates private stat value. This is a real source of confusion and a possible hiding place for bugs.

The active age curve policy is currently:
| pos | curve |
|---|---|
| QB | 82 through age 23; 92 ages 24-31; 82 ages 32-35; then -7/year floor 52 |
| RB | 92 through age 21; 95 ages 22-25; 82 ages 26-27; then -12/year floor 35 |
| WR | 90 through age 22; 94 ages 23-27; 82 ages 28-30; then -9/year floor 45 |
| TE | 86 through age 23; 92 ages 24-29; 78 ages 30-32; then -8/year floor 42 |

Recommended age/dropoff bridge to add next: make age its own auditable bridge with raw age, age bucket, source, decay reason, and position-specific cliff warnings. Age should interact with role/injury: old RB with strong role but weak injury should be capped harder; older WR with still-elite target earning should decline slower; QB age should care about rushing profile separately from passing security.

## Why Results Can Still Look Wonky

| issue | effect |
|---|---|
| Projection source is not independent | Expected/projection features often neutralize to 50, so recent production and role can dominate. |
| Participation/route proxy missing | Many top players carry missing participation warnings, so role confidence is not as strong as it looks. |
| Market default is 50 | Model vs Market edges are inflated and should not be trusted as true trade edge until market imports are real. |
| Young bridge can be visible for low-data players | Young players need review if bridge prior plus missing NFL data creates odd rankings. |
| Ranking sort is keeper-first | A player can rank by keeper_score rather than pure private model value. |
| Age overlay is split from normalization receipts | Age exists in active rows but receipt provenance is not clean enough. |


## Suspicious Case Counts

| case_type | count |
|---|---|
| age_cliff_still_relevant | 4 |
| top_100_missing_market_reference | 96 |
| top_100_missing_participation_proxy | 100 |
| top_100_projection_not_independent | 96 |
| top_150_low_confidence | 15 |
| top_200_blocking_warning | 48 |
| young_bridge_heavy | 145 |


## Suspicious Cases Sample

| case_type | player | pos | rank | confidence | detail |
|---|---|---|---|---|---|
| top_100_projection_not_independent | Justin Jefferson | WR | 1 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Justin Jefferson | WR | 1 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Justin Jefferson | WR | 1 | 77.50 | market_trade_value=50.0 edge=29.5 |
| top_100_projection_not_independent | CeeDee Lamb | WR | 2 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | CeeDee Lamb | WR | 2 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | CeeDee Lamb | WR | 2 | 77.50 | market_trade_value=50.0 edge=28.06 |
| top_100_projection_not_independent | Ja'Marr Chase | WR | 3 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Ja'Marr Chase | WR | 3 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Ja'Marr Chase | WR | 3 | 77.50 | market_trade_value=50.0 edge=27.09 |
| top_100_projection_not_independent | Malik Nabers | WR | 4 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Malik Nabers | WR | 4 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Malik Nabers | WR | 4 | 75.50 | market_trade_value=50.0 edge=27.37 |
| top_100_projection_not_independent | Amon-Ra St. Brown | WR | 5 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Amon-Ra St. Brown | WR | 5 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Amon-Ra St. Brown | WR | 5 | 77.50 | market_trade_value=50.0 edge=26.61 |
| top_100_projection_not_independent | A.J. Brown | WR | 6 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | A.J. Brown | WR | 6 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | A.J. Brown | WR | 6 | 77.50 | market_trade_value=50.0 edge=25.97 |
| top_100_projection_not_independent | Puka Nacua | WR | 7 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Puka Nacua | WR | 7 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Puka Nacua | WR | 7 | 75.50 | market_trade_value=50.0 edge=25.37 |
| top_100_projection_not_independent | Brian Thomas Jr. | WR | 8 | 75.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Brian Thomas Jr. | WR | 8 | 75.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Brian Thomas Jr. | WR | 8 | 75.50 | market_trade_value=50.0 edge=25.78 |
| top_100_projection_not_independent | Bijan Robinson | RB | 9 | 75.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Bijan Robinson | RB | 9 | 75.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Bijan Robinson | RB | 9 | 75.50 | market_trade_value=50.0 edge=25.12 |
| top_100_projection_not_independent | Tyreek Hill | WR | 10 | 70.50 | data_warning_confidence_below_target/injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/missing_snap_counts/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Tyreek Hill | WR | 10 | 70.50 | data_warning_confidence_below_target/injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/missing_snap_counts/stale_lve_scoring_source |
| top_100_missing_market_reference | Tyreek Hill | WR | 10 | 70.50 | market_trade_value=50.0 edge=23.85 |
| top_100_projection_not_independent | Nico Collins | WR | 11 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Nico Collins | WR | 11 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Nico Collins | WR | 11 | 77.50 | market_trade_value=50.0 edge=22.46 |
| top_100_projection_not_independent | DJ Moore | WR | 12 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | DJ Moore | WR | 12 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | DJ Moore | WR | 12 | 77.50 | market_trade_value=50.0 edge=21.06 |
| top_100_projection_not_independent | Jahmyr Gibbs | RB | 13 | 75.50 | committee_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Jahmyr Gibbs | RB | 13 | 75.50 | committee_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Jahmyr Gibbs | RB | 13 | 75.50 | market_trade_value=50.0 edge=20.73 |
| age_cliff_still_relevant | Davante Adams | WR | 14 | 77.50 | age_curve=55.0 keeper=67.38 |
| top_100_projection_not_independent | Davante Adams | WR | 14 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Davante Adams | WR | 14 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Davante Adams | WR | 14 | 77.50 | market_trade_value=50.0 edge=20.58 |
| top_100_projection_not_independent | Stefon Diggs | WR | 15 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Stefon Diggs | WR | 15 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Stefon Diggs | WR | 15 | 77.50 | market_trade_value=50.0 edge=20.19 |
| top_100_projection_not_independent | Garrett Wilson | WR | 16 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Garrett Wilson | WR | 16 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Garrett Wilson | WR | 16 | 77.50 | market_trade_value=50.0 edge=19.61 |
| top_100_projection_not_independent | Drake London | WR | 17 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Drake London | WR | 17 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Drake London | WR | 17 | 77.50 | market_trade_value=50.0 edge=19.14 |
| top_100_projection_not_independent | Mike Evans | WR | 18 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Mike Evans | WR | 18 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Mike Evans | WR | 18 | 77.50 | market_trade_value=50.0 edge=19.62 |
| age_cliff_still_relevant | Keenan Allen | WR | 19 | 77.50 | age_curve=55.0 keeper=66.37 |
| top_100_projection_not_independent | Keenan Allen | WR | 19 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Keenan Allen | WR | 19 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Keenan Allen | WR | 19 | 77.50 | market_trade_value=50.0 edge=19.38 |
| top_100_projection_not_independent | Kenneth Walker III | RB | 20 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Kenneth Walker III | RB | 20 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Kenneth Walker III | RB | 20 | 77.50 | market_trade_value=50.0 edge=18.54 |
| top_100_projection_not_independent | George Pickens | WR | 21 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | George Pickens | WR | 21 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | George Pickens | WR | 21 | 77.50 | market_trade_value=50.0 edge=18.33 |
| top_100_projection_not_independent | Chris Godwin Jr. | WR | 22 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Chris Godwin Jr. | WR | 22 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Chris Godwin Jr. | WR | 22 | 77.50 | market_trade_value=50.0 edge=18.24 |
| top_100_projection_not_independent | Marvin Harrison Jr. | WR | 23 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Marvin Harrison Jr. | WR | 23 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Marvin Harrison Jr. | WR | 23 | 75.50 | market_trade_value=50.0 edge=18.97 |
| top_100_projection_not_independent | Ladd McConkey | WR | 24 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Ladd McConkey | WR | 24 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Ladd McConkey | WR | 24 | 75.50 | market_trade_value=50.0 edge=18.28 |
| top_100_projection_not_independent | DeVonta Smith | WR | 25 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_participation_proxy | DeVonta Smith | WR | 25 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_market_reference | DeVonta Smith | WR | 25 | 77.50 | market_trade_value=50.0 edge=17.78 |
| top_100_projection_not_independent | Tee Higgins | WR | 26 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Tee Higgins | WR | 26 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_market_reference | Tee Higgins | WR | 26 | 77.50 | market_trade_value=50.0 edge=17.79 |
| top_100_projection_not_independent | Courtland Sutton | WR | 27 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Courtland Sutton | WR | 27 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Courtland Sutton | WR | 27 | 77.50 | market_trade_value=50.0 edge=17.62 |
| top_100_projection_not_independent | Michael Pittman Jr. | WR | 28 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Michael Pittman Jr. | WR | 28 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Michael Pittman Jr. | WR | 28 | 77.50 | market_trade_value=50.0 edge=17.59 |
| top_100_projection_not_independent | Brandon Aiyuk | WR | 29 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Brandon Aiyuk | WR | 29 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_market_reference | Brandon Aiyuk | WR | 29 | 77.50 | market_trade_value=50.0 edge=17.2 |
| top_100_projection_not_independent | DK Metcalf | WR | 30 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | DK Metcalf | WR | 30 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | DK Metcalf | WR | 30 | 77.50 | market_trade_value=50.0 edge=16.94 |
| top_100_projection_not_independent | James Cook | RB | 31 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | James Cook | RB | 31 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | James Cook | RB | 31 | 77.50 | market_trade_value=50.0 edge=16.33 |
| top_100_projection_not_independent | Chris Olave | WR | 32 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Chris Olave | WR | 32 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Chris Olave | WR | 32 | 77.50 | market_trade_value=50.0 edge=16.21 |
| top_100_projection_not_independent | Najee Harris | RB | 33 | 77.50 | committee_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Najee Harris | RB | 33 | 77.50 | committee_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Najee Harris | RB | 33 | 77.50 | market_trade_value=50.0 edge=15.61 |
| top_100_projection_not_independent | Zay Flowers | WR | 34 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | Zay Flowers | WR | 34 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | Zay Flowers | WR | 34 | 75.50 | market_trade_value=50.0 edge=16.23 |
| top_100_projection_not_independent | Terry McLaurin | WR | 35 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Terry McLaurin | WR | 35 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Terry McLaurin | WR | 35 | 77.50 | market_trade_value=50.0 edge=16.03 |
| top_100_projection_not_independent | De'Von Achane | RB | 36 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_participation_proxy | De'Von Achane | RB | 36 | 75.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source/young_nfl_bridge_prior_active |
| top_100_missing_market_reference | De'Von Achane | RB | 36 | 75.50 | market_trade_value=50.0 edge=16.13 |
| top_100_projection_not_independent | Jakobi Meyers | WR | 37 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Jakobi Meyers | WR | 37 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |
| top_100_missing_market_reference | Jakobi Meyers | WR | 37 | 77.50 | market_trade_value=50.0 edge=15.5 |
| top_100_projection_not_independent | Amari Cooper | WR | 38 | 70.50 | data_warning_confidence_below_target/local_baseline_projection_not_independent/missing_participation_proxy/missing_snap_counts/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Amari Cooper | WR | 38 | 70.50 | data_warning_confidence_below_target/local_baseline_projection_not_independent/missing_participation_proxy/missing_snap_counts/stale_lve_scoring_source |
| top_100_missing_market_reference | Amari Cooper | WR | 38 | 70.50 | market_trade_value=50.0 edge=15.8 |
| top_100_projection_not_independent | Jerry Jeudy | WR | 39 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_participation_proxy | Jerry Jeudy | WR | 39 | 77.50 | local_baseline_projection_not_independent/missing_participation_proxy/stale_lve_scoring_source |
| top_100_missing_market_reference | Jerry Jeudy | WR | 39 | 77.50 | market_trade_value=50.0 edge=14.33 |
| top_100_projection_not_independent | Calvin Ridley | WR | 40 | 77.50 | injury_risk/local_baseline_projection_not_independent/missing_participation_proxy/route_role_fragility/stale_lve_scoring_source |


## What I Would Fix Before Trusting Rankings

| priority | fix | why |
|---|---|---|
| 1 | Create an explicit age/dropoff bridge | Age currently works but provenance is split. This needs a clean receipt and tests. |
| 2 | Separate pure Model Value board from Keeper Decision board | Current ranking is keeper-first. That may not match how you mentally evaluate asset quality. |
| 3 | Add confidence qualification to top rankings | Low-confidence or blocking young players should not appear as normal ranked assets. |
| 4 | Import or explicitly accept independent projections | Projection value is currently mostly a baseline, so forward-looking value is weak. |
| 5 | Improve participation/route/workload sources | Role is a core model pillar; missing participation proxy is too common. |
| 6 | Import real trade market or hide edge claims | Market value at default 50 makes edge labels misleading. |
| 7 | Run named-player source truth audit after every model change | This is how Kaleb-type hidden bugs get caught early. |


## Decision Readiness

Do not mark this model final decision-ready yet. It is usable for inspection and debugging, and the latest patch prevents low-confidence young/no-NFL-evidence players from being treated as normal shop candidates. But the rankings still need source provenance cleanup, age/dropoff bridge receipts, and projection/role coverage before I would personally trust them for money decisions.
