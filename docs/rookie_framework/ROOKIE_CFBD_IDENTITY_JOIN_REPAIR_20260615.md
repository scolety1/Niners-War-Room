# Rookie CFBD Historical Identity / Join Repair Audit - 2026-06-15

## Executive verdict

Join repair verdict: YELLOW/GREEN.

The repair pass materially improved the CFBD historical feature join and eliminated the 2010 draft-class outside-cache blocker by fetching the approved 2009 CFBD regular-season endpoints. The remaining blocker is identity coverage, not API feasibility.

Verdicts:

| Area | Verdict | Notes |
| --- | --- | --- |
| Join repair | YELLOW/GREEN | matched rows improved from 884 to 980, but 129 rows remain unresolved |
| 2009 fetch | GREEN | 4 approved endpoints available; no failed endpoint rows |
| Leakage safety | GREEN | no tuning, no labels-as-features, no API secret exposure |
| Enriched baseline readiness | YELLOW | ready for a repaired-baseline audit with unresolved-row policy; not ready for tuning |

No tuning, v2 board, production ranking, private-score overwrite, app wiring, probability, band, hidden sort key, or promoted artifact was created.

## Inputs inspected

- `local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615/cfbd_drafted_rookie_feature_join_v1_20260615.csv`
- `local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615/cfbd_player_season_features_v1_20260615.csv`
- `local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615/cfbd_historical_fetch_manifest_v1_20260615.csv`
- `local_exports/rookie_framework/cfbd_identity_join_repair_20260615/`

## 2009 fetch result

The 2010 draft class needs time-safe 2009 college stats. The approved narrow 2009 fetch was required because the prior cache covered 2010-2023 only.

Approved 2009 endpoint results:

| Endpoint/category | Rows | Status |
| --- | ---: | --- |
| passing | 3,122 | fetched, then cache-hit on rebuild |
| rushing | 6,950 | fetched, then cache-hit on rebuild |
| receiving | 8,585 | fetched, then cache-hit on rebuild |
| team denominators | 7,080 | fetched, then cache-hit on rebuild |

The repair export built 1,881 2009 player-season feature rows. API keys were not printed, written to export files, or committed.

## Before / after coverage

| Metric | Before | After |
| --- | ---: | ---: |
| matched | 884 | 980 |
| unmatched | 147 | 129 |
| outside-cache | 78 | 0 |
| duplicate-selected | 8 | 8 |
| excluded | 0 | 0 |

Net result:

- 96 rows were repaired.
- 78 outside-cache rows were resolved as a class.
- 18 of the 2010 draft-class rows remain unresolved after 2009 was added.
- Duplicate-selected rows remain visible for review instead of being hidden.

## Repair classifications

| Classification | Rows | Action |
| --- | ---: | --- |
| already matched | 876 | kept |
| duplicate candidate existing | 8 | kept with duplicate review export |
| ID or exact alias repaired | 56 | repaired |
| position mismatch repaired | 33 | repaired |
| alias issue repaired | 7 | repaired |
| CFBD missing row or alias not deterministic | 82 | not repaired |
| CFBD missing row or no college stat profile | 44 | not repaired |
| position mismatch manual review | 3 | not repaired |

Safe repairs were limited to deterministic evidence:

- exact normalized name + expected season + position;
- exact normalized name + expected season + college/team with CFBD position mismatch;
- first-initial/last-name + expected season + college/team + position when unique.

No player-specific scoring/tuning rule was added.

## 2010 draft-class coverage after 2009 fetch

| Status | Rows |
| --- | ---: |
| matched exact after repair | 56 |
| matched position mismatch repaired | 4 |
| unresolved CFBD missing/alias manual review | 12 |
| unresolved CFBD missing row | 6 |

The 2010 class is no longer outside-cache. It is still not fully clean because 18 rows need manual identity/source review.

Examples of unresolved 2010 rows:

- Jermaine Gresham, TE, Oklahoma: college/team and position exist, but no deterministic player identity match.
- Rob Gronkowski, TE, Arizona: college/team and position exist, but no deterministic player identity match.
- Jahvid Best, RB, California: no deterministic CFBD feature row found.
- Andre Roberts, WR, The Citadel: no deterministic CFBD feature row found.
- John Skelton, QB, Fordham: no deterministic CFBD feature row found.

## Duplicate candidate audit

The duplicate review export contains 8 rows:

- Chris Givens, WR, Wake Forest;
- Chris Harper, WR, Kansas St.;
- James White, RB, Wisconsin;
- Michael Thomas, WR, Ohio St. / selected candidate team Southern Miss;
- Joe Williams, RB, Utah;
- Kevin Harris, RB, South Carolina;
- Justin Shorter, WR, Florida;
- Zach Evans, RB, Mississippi / selected candidate team Ole Miss.

These remain visible for manual QA before tuning. The Michael Thomas row is especially important because the selected CFBD candidate team does not match the drafted label college and should not be trusted without review.

## Unresolved rows

Unresolved rows after repair: 129.

Buckets:

- 82 `cfbd_missing_row_or_alias_not_deterministic`: college/team and position evidence exists but no deterministic player identity match.
- 44 `cfbd_missing_row_or_no_college_stat_profile`: no deterministic CFBD feature row found for expected season/name/position.
- 3 `position_mismatch_manual_review`: same normalized name exists, but college/team evidence is not deterministic.

These rows should be treated as missing-feature rows or manual-review rows for the next enriched baseline audit, not silently zero-filled as valid college production.

## Enriched baseline readiness

The enriched baseline is not tuning-ready yet.

It is ready for a separate repaired-baseline audit if that audit explicitly:

- excludes or flags the 129 unresolved rows;
- preserves duplicate-review warnings;
- treats repaired position mismatches as manual-review context;
- confirms no labels, outcomes, ADP, market, public rankings, projections, or known results enter feature construction;
- reports metrics both with and without unresolved rows.

Tuning should wait until that repaired-baseline audit is GREEN.

## Exports created

Local-only exports under:

`local_exports/rookie_framework/cfbd_identity_join_repair_20260615/`

Files:

- `raw_cfbd_2009_csv/player_stats_season_2009_regular_passing.csv`
- `raw_cfbd_2009_csv/player_stats_season_2009_regular_rushing.csv`
- `raw_cfbd_2009_csv/player_stats_season_2009_regular_receiving.csv`
- `raw_cfbd_2009_csv/team_stats_season_2009_regular.csv`
- `cfbd_2009_fetch_manifest_20260615.csv`
- `cfbd_2009_player_season_features_20260615.csv`
- `cfbd_identity_join_repair_audit_20260615.csv`
- `cfbd_drafted_rookie_feature_join_repaired_20260615.csv`
- `cfbd_duplicate_candidate_review_20260615.csv`
- `cfbd_identity_join_repair_summary_20260615.csv`
- `README_ROOKIE_CFBD_IDENTITY_JOIN_REPAIR_20260615.md`

These exports are local-only and were not committed.

## Anti-cheat / leakage audit

| Check | Result |
| --- | --- |
| API key not printed, logged, exported, or committed | PASS |
| 2009 fetch limited to approved endpoints only | PASS |
| No tuning performed | PASS |
| No v2 board created | PASS |
| Labels used only for join audit, not feature construction | PASS |
| Outcome labels not used as features | PASS |
| ADP/market/rank/projection fields not used | PASS |
| No player/school/team/class-specific tuning rule added | PASS |
| No production/app/probability/band artifact created | PASS |
| `data/` not committed | PASS |
| `local_exports/` not committed | PASS |

## Commands run

- `git status --short`
- `git rev-parse HEAD`
- `git branch --show-current`
- inspection of CFBD v1 join, feature, and manifest exports
- `python tests\test_rookie_cfbd_identity_join_repair_v1.py`
- `python -m py_compile scripts\rookie_framework\audit_rookie_cfbd_identity_join_repair_v1.py tests\test_rookie_cfbd_identity_join_repair_v1.py`
- `python scripts\rookie_framework\audit_rookie_cfbd_identity_join_repair_v1.py`
- classification, duplicate, manifest, and 2010-class coverage inspections over local repair exports

## Recommended next rookie-only task

Run a repaired enriched-baseline audit, not tuning. The audit should decide how to treat:

- 129 unresolved rows;
- 8 duplicate-selected rows;
- position-mismatch repaired rows;
- manual-review rows with missing deterministic CFBD identity.

Only after that audit is GREEN should tuning be considered.
