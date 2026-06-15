# Sprint 5CH: Earliest Historical Boundary Source Feasibility Audit

Outcome lane: veteran outcome probability column path only

Verdict: `YELLOW_2010_DUPLICATE_KEY_BLOCKER_NO_REBUILD`

Sprint type: `SOURCE_BOUNDARY_AUDIT_ONLY_NO_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5CH audits the next safe historical expansion boundary after the committed and audited 2012-2013 local historical feature/label package. This sprint does not build a new feature/label package, train models, generate probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, edit `data/`, edit `local_exports/`, or create promoted artifacts.

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5CF_LOCAL_ONLY_2012_2013_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5CG_AUDIT_2012_2013_HISTORICAL_FEATURE_LABEL_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5CE_R2_2011_2012_POSITION_REPAIR_REAUDIT.md`
- `scripts/outcome_probability/build_sprint_5cf_2012_2013_historical_feature_label_rebuild.py`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

No local-only 5CH export package was created because this sprint was completed with read-only inspection and the lane instruction was to avoid touching `local_exports/`.

## 2. Historical Boundary Decision

Committed and audited historical feature/label packages now cover:

- 2018-2019
- 2016-2017
- 2014-2015
- 2012-2013

The next chronological target after 2012-2013 is a 2010-2011 historical feature/label rebuild package:

| Target season | Required prior feature source season | Required label source season | Boundary result |
| ---: | ---: | ---: | --- |
| 2010 | completed 2009 season | final 2010 stats | source coverage appears feasible |
| 2011 | completed 2010 season | final 2011 stats with approved 5CE-R2 overlay if needed | blocked by 2010 duplicate key |

Recommendation: do not build a full 2010-2011 package yet. The boundary is useful, but the 2010 source season has one unresolved duplicate `player_id + season + week + season_type` key. Because 2010 would be the prior-season feature source for target 2011, the duplicate must be repaired or explicitly adjudicated before a 2010-2011 package is proposed.

## 3. 2009 Coverage

2009 coverage exists in the local `player_stats.csv` source.

| Season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate extra rows | Blank offensive position rows | Source result |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2009 | 5242 | 5035 | 1-17 | 563 | 0 | 0 | GREEN for source coverage |

2009 is required if the next full package includes target season 2010, because 2010 features would use completed 2009 source data only.

2009 does not currently block the boundary.

## 4. 2010 Duplicate-Key Audit

2010 coverage exists, but it is not GREEN because of one duplicate player-week key.

| Season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate extra rows | Blank offensive position rows | Source result |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2010 | 5204 | 4988 | 1-17 | 580 | 1 | 0 | YELLOW |

Duplicate key:

| Player ID | Player | Team | Season | Week | Season type | Duplicate rows identical? | Blocker |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| `00-0026498` | Matthew Stafford | DET | 2010 | 8 | REG | no | yes |

The two Matthew Stafford rows are not identical. One row carries passing activity, while the other carries no listed raw passing/rushing/receiving activity but has imported fantasy totals. Because fantasy totals remain quarantined, this duplicate cannot be silently summed, ignored, or repaired inside a rebuild sprint without a separate source-safe duplicate-key repair audit.

2010 therefore blocks use as a prior feature source for target 2011 until a later sprint resolves the duplicate deterministically.

## 5. 2011 Source Registration After 5CE-R2

2011 source registration remains GREEN after applying the approved 5CE-R2 audit-time position repair overlay.

| Season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate extra rows | Blank offensive position rows after repair | Source result |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2011 | 5301 | 5091 | 1-17 | 586 | 0 | 0 | GREEN |

5CE-R2 repairs considered:

| Player ID | Player | Repair position | Repair scope |
| --- | --- | --- | --- |
| `00-0027567` | Steve Maneri | TE | affected 2011 blank offensive rows |
| `00-0028543` | Jeff Maehl | WR | affected 2011 blank offensive rows |

2011 being GREEN is useful for the historical boundary, but it does not remove the 2010 duplicate-key blocker for target 2011 features.

## 6. Identity, Team, And Position

Identity/team/position result:

| Season | Missing player ID | Missing team | Missing position | Missing position group | Blank offensive position rows | Result |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2009 | 0 | 0 | 0 | 0 | 0 | pass |
| 2010 | 0 | 0 | 0 | 0 | 0 | pass, except duplicate-key blocker |
| 2011 after 5CE-R2 overlay | 0 | 0 | 0 | 0 | 0 | pass |

No additional blank/missing position repair is currently required for 2009, 2010, or 2011 after the approved 5CE-R2 overlay. The remaining blocker is duplicate-key repair for 2010, not position repair.

## 7. First-Down Completeness

Rushing and receiving first-down completeness result: pass.

| Season | Modeled REG rows | Missing rushing first downs | Missing receiving first downs | Result |
| ---: | ---: | ---: | ---: | --- |
| 2009 | 4712 | 0 | 0 | pass |
| 2010 | 4685 | 0 | 0 | pass |
| 2011 after 5CE-R2 overlay | 4808 | 0 | 0 | pass |

First-down availability does not block the next boundary.

## 8. Forbidden-Field Quarantine

Forbidden-field quarantine result: pass.

The local source contains quarantined fields that must remain excluded from any future feature package:

- `fantasy_points`
- `fantasy_points_ppr`
- `passing_epa`
- `rushing_epa`
- `receiving_epa`
- `dakota`
- `wopr`
- `racr`
- `pacr`
- `target_share`
- `air_yards_share`

No ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, same-season final stats as preseason features, or label supplement sources are approved for prediction features.

The 2010 Matthew Stafford duplicate is especially sensitive because one duplicate row appears to carry only quarantined fantasy total values. This reinforces the need for a separate duplicate-key repair audit before using 2010 as a feature source season.

## 9. Return-Stat Limitation

Return-stat limitation remains unchanged.

| Field | Available in local `player_stats.csv`? | Approved for source-safe NWR reconstruction? |
| --- | --- | --- |
| `special_teams_tds` | yes | no, not granular enough for current source-safe policy |
| `return_yards` | no | no |
| `return_tds` | no | no |
| `punt_return_yards` | no | no |
| `kickoff_return_yards` | no | no |
| `punt_return_tds` | no | no |
| `kickoff_return_tds` | no | no |

Granular return yards and return touchdowns remain unavailable from `player_stats.csv` alone. Return scoring remains excluded unless a later sprint registers and audits a legal granular source.

## 10. Recommendation

5CH recommendation: YELLOW.

Reason:

- 2009 source coverage exists and appears usable.
- 2011 is GREEN after the 5CE-R2 repair overlay.
- 2010 has one unresolved duplicate player-week key for Matthew Stafford, and the duplicate rows are not identical.

The next intended full boundary should be 2010-2011, but it is not approved to build yet.

Recommended next safe sprint: Sprint 5CH-R - deterministic 2010 duplicate-key repair feasibility and re-audit. That sprint should decide whether the Matthew Stafford 2010 week 8 duplicate can be repaired using source-safe local evidence without copying quarantined fantasy totals or making manual guesses.

If 2010 duplicate-key repair passes, HQ can separately approve a future 2010-2011 local-only feature/label rebuild package.

## 11. Release Stance

5CH does not approve a new feature/label package.

5CH does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 12. Checks

Checks run:

- required repo/branch/status/log preflight passed
- read-only local `player_stats.csv` source inventory completed
- `git diff --check` passed

No Python files were changed in 5CH, so `python -m py_compile` and Ruff were not required. Pytest was not required because no code or tests changed.
