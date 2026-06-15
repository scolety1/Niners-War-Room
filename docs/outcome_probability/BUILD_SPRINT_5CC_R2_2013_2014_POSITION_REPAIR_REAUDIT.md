# Sprint 5CC-R2: 2013-2014 Position Repair Patch And Re-Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_SOURCE_REGISTRATION_AFTER_REPAIR_REBUILD_STILL_BLOCKED`

Sprint type: `DETERMINISTIC_REPAIR_REAUDIT_NO_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5CC-R2 applies a narrow deterministic repair overlay for the 2013-2014 blank `position` / `position_group` offensive rows identified in 5CB and approved as repairable in 5CC-R, then re-audits 2013-2014 source registration. This sprint does not edit raw `player_stats.csv`, generate feature/label rebuild rows, train models, generate probabilities, create coarse bands, create app-readable probability/band/status outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Repair evidence:

- `docs/outcome_probability/BUILD_SPRINT_5CC_R_2013_2014_POSITION_REPAIR_FEASIBILITY_AUDIT.md`
- local DynastyProcess player IDs identity crosswalk
- local Sleeper-to-GSIS identity bridge

No internet lookup was performed. No manual guessing was used.

## 2. Repair Mechanism

Repair is an audit-time deterministic overlay, not a raw data edit.

Approved mapping:

| Player ID | Player | Repair position | Repair grain |
| --- | --- | --- | --- |
| `00-0027567` | Steve Maneri | TE | all affected 2013-2014 blank-position offensive rows for this `player_id` |
| `00-0028543` | Jeff Maehl | WR | all affected 2013-2014 blank-position offensive rows for this `player_id` |
| `00-0029675` | Trent Richardson | RB | all affected 2013-2014 blank-position offensive rows for this `player_id` |

The overlay is limited to rows where:

1. season is 2013 or 2014;
2. `player_id` is one of the approved three IDs;
3. `position` or `position_group` is blank;
4. the row has offensive activity.

The repaired position is used only for source registration and normal legal position eligibility. It is not a new model signal beyond the ordinary legal `position` field.

## 3. Local-Only Re-Audit Export

Created local-only export package:

`local_exports/outcome_probability/sprint_5cc_r2_2013_2014_position_repair_reaudit/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5cc_r2.json` | run metadata, repair mapping, verdicts, release blockers | no |
| `position_repair_applied_rows.csv` | rows repaired by overlay | no |
| `position_repair_by_player.csv` | repair counts and source evidence by player | no |
| `source_registration_reaudit_after_repair.csv` | re-audited 2013-2014 source-registration checks | no |
| `README_SPRINT_5CC_R2.md` | local-only package summary | no |

All outputs are internal-only and not app-readable.

## 4. Rows Repaired

| Player ID | Player | Position | Repaired rows | Seasons |
| --- | --- | --- | ---: | --- |
| `00-0027567` | Steve Maneri | TE | 3 | 2013, 2014 |
| `00-0028543` | Jeff Maehl | WR | 9 | 2013, 2014 |
| `00-0029675` | Trent Richardson | RB | 33 | 2013, 2014 |
| Total |  |  | 45 | 2013, 2014 |

Raw data modified: no.

Manual guesses used: no.

Forbidden sources used: no.

## 5. Source Registration Re-Audit

| Source season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate extra rows | Blank offensive position rows after repair | Registration verdict after repair |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2013 | 5231 | 5022 | 1-17 | 591 | 0 | 0 | GREEN |
| 2014 | 5350 | 5129 | 1-17 | 589 | 0 | 0 | GREEN |

2013 source registration after repair: GREEN.

2014 source registration after repair: GREEN.

This is still not approval to run the 2014-2015 rebuild. The next rebuild sprint requires separate HQ approval.

## 6. Identity, Team, Position, And Duplicate Keys

After repair:

| Source season | Missing player ID | Missing team/recent_team | Missing position | Missing position_group | Duplicate key extra rows |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2013 | 0 | 0 | 0 | 0 | 0 |
| 2014 | 0 | 0 | 0 | 0 | 0 |

Identity/team/position result: pass.

Duplicate-key result: pass.

## 7. First-Down Completeness

| Source season | Rushing first downs available | Rushing first downs missing | Receiving first downs available | Receiving first downs missing |
| ---: | --- | ---: | --- | ---: |
| 2013 | yes | 0 | yes | 0 |
| 2014 | yes | 0 | yes | 0 |

First-down completeness result: pass.

## 8. Forbidden-Field Quarantine

Forbidden/quarantined source fields remain excluded from any repair logic:

- `fantasy_points`
- `fantasy_points_ppr`
- `passing_epa`, `rushing_epa`, `receiving_epa`
- `dakota`
- `wopr`, `racr`, `pacr`
- `target_share`, `air_yards_share`
- ADP
- public rankings
- projections
- consensus
- market values
- trade values/calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- same-season final stats as preseason features
- label supplement sources as prediction features

Forbidden-field/quarantine result: pass.

## 9. Release Stance

5CC-R2 does not perform the 2014-2015 feature/label rebuild.

5CC-R2 does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 10. Recommended Next Safe Sprint

Recommended next safe sprint, if HQ approves: Sprint 5CC-R3 or 5CC restart - build the local-only 2014-2015 historical feature/label rebuild package using the deterministic position repair overlay and the same quarantine/release blockers.

Do not start the rebuild until HQ explicitly approves that sprint.

## 11. Checks

Checks run:

- local CSV re-audit completed with no downloads and no package installation
- `git diff --check` passed

Ruff was not required because no tracked Python file changed in 5CC-R2. Pytest was not required because no tracked code or test file changed in 5CC-R2.
