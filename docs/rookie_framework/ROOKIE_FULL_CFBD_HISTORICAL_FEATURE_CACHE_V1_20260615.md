# Rookie Full CFBD Historical Feature Cache v1 - 2026-06-15

## Executive verdict

Verdict: YELLOW/GREEN.

The CFBD historical feature cache build is GREEN for source/API feasibility and GREEN for local-only feature construction. It is YELLOW for immediate enriched tuning readiness because identity join repair is still needed before the enriched baseline should be used for model tuning.

The successful 2010/2015/2020 sample was enough to proceed with a controlled 2010-2023 CFBD cache for the approved endpoints only:

- `/stats/player/season` with `category=passing`
- `/stats/player/season` with `category=rushing`
- `/stats/player/season` with `category=receiving`
- `/stats/season` for team denominator stats

No API key was printed, logged, written to exports, or committed. No tuning, v2 board, production ranking, private-score overwrite, app wiring, probability, band, hidden sort key, or promoted artifact was created.

## Cache build result

| Item | Result |
| --- | ---: |
| Approved years fetched/cached | 2010-2023 |
| Approved endpoint requests | 56 |
| Successful endpoint caches | 56 |
| Failed endpoint caches | 0 |
| Player feature rows | 44,961 |
| Team denominator rows | 1,785 |
| Drafted QB/RB/WR/TE join rows | 1,109 |

The first full run exceeded the shell time window after the cache had landed. The second run used `--skip-fetch` to rebuild derived outputs from local cache only.

## Row-count checks by year

| Year | Passing | Rushing | Receiving | Team denominators | Total cached rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2010 | 3,248 | 7,190 | 8,945 | 7,080 | 26,463 |
| 2011 | 3,325 | 7,330 | 9,410 | 7,080 | 27,145 |
| 2012 | 3,738 | 8,115 | 10,540 | 7,316 | 29,709 |
| 2013 | 4,319 | 9,140 | 12,460 | 7,375 | 33,294 |
| 2014 | 4,277 | 9,730 | 12,625 | 7,552 | 34,184 |
| 2015 | 4,508 | 10,030 | 12,840 | 7,552 | 34,930 |
| 2016 | 4,648 | 10,235 | 13,020 | 8,064 | 35,967 |
| 2017 | 4,578 | 10,450 | 12,815 | 8,187 | 36,030 |
| 2018 | 5,257 | 11,700 | 14,195 | 8,187 | 39,339 |
| 2019 | 4,914 | 10,755 | 13,520 | 8,190 | 37,379 |
| 2020 | 3,227 | 7,200 | 9,465 | 7,990 | 27,882 |
| 2021 | 4,732 | 10,555 | 13,625 | 8,190 | 37,102 |
| 2022 | 7,266 | 16,115 | 20,915 | 8,253 | 52,549 |
| 2023 | 6,867 | 15,070 | 19,875 | 8,376 | 50,188 |

## Feature families built

Built from source-safe CFBD factual regular-season rows:

- QB passing production: yards, TDs, attempts, completions, interceptions;
- QB/RB rushing production: yards, TDs, attempts;
- RB/WR/TE receiving production: yards, TDs, receptions;
- team passing/rushing denominator stats;
- same-season market-share/dominator-style features:
  - passing yard share;
  - passing attempt share;
  - passing TD share;
  - rushing yard share;
  - rushing attempt share;
  - rushing TD share;
  - receiving yard share;
  - reception share;
  - receiving TD share.

Share fields were populated for 31,948 player-season rows. Every player-season feature row is marked:

- `promotion_status=local_feature_cache_only`
- `production_allowed=no`

## Drafted pool join coverage

The drafted-pool join is time-safe: a draft year uses `draft_year - 1` as the expected college feature season. The build did not use future stats, outcomes, labels, ADP, market values, public rankings, projections, or player-specific tuning rules as features.

Overall join statuses:

| Status | Rows |
| --- | ---: |
| `matched_name_position_season` | 876 |
| `matched_with_duplicate_candidate_selection` | 8 |
| `unmatched_name_position_season` | 147 |
| `blocked_expected_season_outside_cache` | 78 |

Match rate including 2010 draft class: 884 / 1,109 = 79.7%.

Match rate excluding 2010 draft class, whose expected 2009 college season was outside the approved cache window: 884 / 1,031 = 85.7%.

By position:

| Position | Matched | Duplicate-selected | Unmatched | Outside cache |
| --- | ---: | ---: | ---: | ---: |
| QB | 136 | 0 | 11 | 13 |
| RB | 229 | 4 | 54 | 15 |
| WR | 355 | 4 | 47 | 29 |
| TE | 156 | 0 | 35 | 21 |

By draft year:

| Draft year | Result |
| --- | --- |
| 2010 | 78 outside-cache rows because expected CFBD feature season is 2009 |
| 2011 | 56 matched, 26 unmatched |
| 2012 | 66 matched/duplicate-selected, 11 unmatched |
| 2013 | 66 matched/duplicate-selected, 14 unmatched |
| 2014 | 62 matched/duplicate-selected, 15 unmatched |
| 2015 | 63 matched, 16 unmatched |
| 2016 | 60 matched/duplicate-selected, 17 unmatched |
| 2017 | 74 matched/duplicate-selected, 9 unmatched |
| 2018 | 70 matched, 13 unmatched |
| 2019 | 75 matched, 5 unmatched |
| 2020 | 72 matched, 6 unmatched |
| 2021 | 67 matched, 9 unmatched |
| 2022 | 73 matched/duplicate-selected, 6 unmatched |
| 2023 | 80 matched/duplicate-selected, 0 unmatched |

## Readiness decision

Manual 2010-2019 file backfill for basic college production and team denominators is now avoidable. CFBD can supply the core source-safe feature families locally after cached fetch.

Enriched baseline/tuning is not ready yet. The feature cache is ready, but a join-repair pass should happen first:

- 147 drafted-pool rows are unmatched by normalized name + position + expected feature season.
- Some important misses may be alias/name issues, transfer/team issues, or CFBD position differences.
- 78 rows from the 2010 draft class require 2009 college features, which were outside the approved 2010-2023 fetch range.
- Duplicate-selected matches need manual/ID QA before tuning.

Recommended readiness:

- Feature cache: GREEN.
- Feature-family availability: GREEN for basic CFBD production/team/share features.
- Join coverage: YELLOW.
- Enriched baseline: YELLOW after identity repair.
- Tuning: RED until identity repair and 2010/2009 policy decision are complete.

## Remaining missing feature families

CFBD did not provide these high-value feature families in the approved endpoint set:

- route participation / YPRR;
- YAC and yards after contact;
- missed tackles forced;
- pass protection;
- contested catch / contested target rates;
- historical injury history;
- historical ADP/market overlay, which must remain display-only.

## Exports created

Local-only exports under:

`local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615/`

Files:

- `raw_cfbd_csv/player_stats_season_{year}_regular_{category}.csv`
- `raw_cfbd_csv/team_stats_season_{year}_regular.csv`
- `cfbd_historical_fetch_manifest_v1_20260615.csv`
- `cfbd_player_season_features_v1_20260615.csv`
- `cfbd_team_season_denominators_v1_20260615.csv`
- `cfbd_drafted_rookie_feature_join_v1_20260615.csv`
- `cfbd_drafted_rookie_join_coverage_v1_20260615.csv`
- `README_CFBD_HISTORICAL_FEATURE_CACHE_V1_20260615.md`

These exports are local-only and were not committed.

## Anti-cheat / leakage audit

| Check | Result |
| --- | --- |
| API key not printed, logged, exported, or committed | PASS |
| Fetch limited to 2010-2023 approved endpoints only | PASS |
| No tuning performed | PASS |
| No v2 board created | PASS |
| No production ranking/app/probability/band artifact created | PASS |
| Labels used only for drafted-pool join/coverage, not feature construction | PASS |
| `draft_year - 1` time-safe college season rule applied | PASS |
| ADP/market/rank/projection fields not used | PASS |
| No player/team/school/class-specific tuning rule added | PASS |
| `data/` not committed | PASS |
| `local_exports/` not committed | PASS |

## Commands run

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- inspection of expanded historical labels and prior CFBD sample exports
- `python tests\test_rookie_cfbd_historical_feature_cache_v1.py`
- `python scripts\rookie_framework\build_rookie_cfbd_historical_feature_cache_v1.py`
- `python scripts\rookie_framework\build_rookie_cfbd_historical_feature_cache_v1.py --skip-fetch`
- row-count, join-coverage, and safety inspections over generated local exports

## Recommended next rookie-only task

Run a CFBD historical identity/join repair audit before tuning. It should focus on:

- alias repair for unmatched rows;
- CFBD position mismatch review;
- transfer/team context review;
- duplicate candidate review;
- a policy decision on whether to approve a narrow 2009 fetch for the 2010 draft class.

Only after that repair audit is GREEN should the enriched baseline be rerun for tuning readiness.
