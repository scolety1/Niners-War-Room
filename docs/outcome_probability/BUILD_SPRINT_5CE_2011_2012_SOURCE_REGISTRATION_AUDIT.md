# Sprint 5CE: 2011-2012 Source Registration Audit

Outcome lane: veteran outcome probability column path only

Verdict: `YELLOW_SOURCE_REGISTRATION_BLOCKER_REBUILD_NOT_APPROVED`

Sprint type: `SOURCE_REGISTRATION_AUDIT_NO_REBUILD_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CE audits whether completed source seasons 2011 and 2012 can be source-registered for future target seasons 2012 and 2013. This sprint used only existing local `player_stats.csv` evidence. It did not download data, install packages, generate feature/label rebuild rows, train models, generate probabilities, create coarse bands, create app-readable status/probability/band outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, edit raw data, or create promoted artifacts.

Read-only source evidence:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Local-only inventory export:

`local_exports/outcome_probability/sprint_5ce_2011_2012_source_registration_audit/`

## 2. Source Registration Summary

| Source season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate player-week extra rows | Missing player ID | Missing team | Missing position | Missing position group | Blank offensive position rows | Verdict |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2011 | 5301 | 5091 | 1-17 | 586 | 0 | 0 | 0 | 3 | 3 | 3 | YELLOW |
| 2012 | 5354 | 5150 | 1-17 | 603 | 0 | 0 | 0 | 21 | 21 | 20 | YELLOW |

5CE verdict is YELLOW because both 2011 and 2012 have unresolved blank `position` / `position_group` rows with offensive activity. Per the gated autorun contract, 5CF and 5CG must not run.

## 3. Blank Offensive Position Rows

Affected blank-position offensive rows:

| Season | Player ID | Player | Team | Blank offensive rows |
| ---: | --- | --- | --- | ---: |
| 2011 | `00-0027567` | Steve Maneri | KC | 2 |
| 2011 | `00-0028543` | Jeff Maehl | HOU | 1 |
| 2012 | `00-0027567` | Steve Maneri | KC | 5 |
| 2012 | `00-0029675` | Trent Richardson | CLE | 15 |
| Total |  |  |  | 23 |

The 2012 season has 21 total blank `position` / `position_group` regular-season rows, of which 20 have offensive activity. The source registration blocker is the offensive subset.

No source-safe repair overlay was applied in 5CE. Any repair would require a later feasibility sprint and HQ approval.

## 4. Field Availability

Passing fields are present with no modeled-row missingness for 2011 and 2012:

- `completions`
- `attempts`
- `passing_yards`
- `passing_tds`
- `interceptions`

Rushing fields are present with no modeled-row missingness for 2011 and 2012:

- `carries`
- `rushing_yards`
- `rushing_tds`
- `rushing_first_downs`
- `rushing_fumbles_lost`

Receiving fields are present with no modeled-row missingness for 2011 and 2012:

- `receptions`
- `targets`
- `receiving_yards`
- `receiving_tds`
- `receiving_first_downs`
- `receiving_fumbles_lost`

Fumble-lost fields are present with no modeled-row missingness for 2011 and 2012:

- `rushing_fumbles_lost`
- `receiving_fumbles_lost`
- `sack_fumbles_lost`

Special-teams/return limitation:

- `special_teams_tds` is present but remains excluded from future source registration features.
- granular `return_tds` is not present.
- granular `return_yards` is not present.
- Return scoring remains excluded from source-safe NWR reconstruction unless a later approved source provides granular, legal fields.

## 5. First-Down Availability

First-down availability is otherwise GREEN:

| Source season | Modeled REG rows | Missing rushing first downs | Missing receiving first downs | Result |
| ---: | ---: | ---: | ---: | --- |
| 2011 | 4805 | 0 | 0 | pass |
| 2012 | 4818 | 0 | 0 | pass |

The YELLOW verdict is not caused by first-down missingness. It is caused by unresolved blank offensive `position` / `position_group` rows.

## 6. Duplicate Keys And Identity

Duplicate-key result: pass.

| Source season | Duplicate player-week extra rows |
| ---: | ---: |
| 2011 | 0 |
| 2012 | 0 |

Identity/team result: pass for `player_id` and `recent_team`.

Position result: fail/blocker until the blank offensive position rows are repaired or the window is bypassed.

## 7. Forbidden-Field Quarantine

Forbidden/quarantined fields are present in the local source and must remain excluded from future features:

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

No ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, same-season final stats as preseason features, or label supplement sources were approved for prediction features.

## 8. Gate Decision

2011 source registration: YELLOW.

2012 source registration: YELLOW.

Future 2012-2013 target expansion is not approved for rebuild or modeling now.

Per the autorun contract, 5CF and 5CG are skipped because 5CE is YELLOW.

## 9. Release/Display Stance

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting usage and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but 5CE creates no app-readable status table and approves no numeric display.

## 10. Recommended Next Safe Sprint

Recommended next safe sprint: 5CE-R - 2011-2012 blank offensive position repair feasibility audit.

That sprint should determine whether local source-safe identity/roster evidence can deterministically repair:

- Steve Maneri, 2011 and 2012
- Jeff Maehl, 2011
- Trent Richardson, 2012

If source-safe repair evidence does not exist, keep 2011-2012 blocked and do not run the 2012-2013 rebuild.

## 11. Checks

Checks run:

- local read-only inventory of `player_stats.csv` for 2011 and 2012 completed
- local-only export package created under `local_exports/outcome_probability/sprint_5ce_2011_2012_source_registration_audit/`
- no downloads, package installs, modeling, probability generation, app output, ranking/sorting output, or promoted artifacts were created
