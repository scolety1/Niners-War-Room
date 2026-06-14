# Sprint 5CB: 2013-2014 Source Registration Audit

Outcome lane: veteran outcome probability column path only

Verdict: `YELLOW_SOURCE_REGISTRATION_BLOCKED_BY_UNRESOLVED_POSITION_MISSINGNESS`

Sprint type: `SOURCE_REGISTRATION_AUDIT_NO_FEATURE_LABEL_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5CB audits whether 2013 and 2014 nflverse-style `player_stats.csv` source seasons are clean enough to support a later 2014-2015 veteran Outcome historical feature/label rebuild. This sprint is source registration and inventory only. It does not generate feature rows, generate label rows, train models, generate probabilities, create coarse bands, create app-readable status/probability/band outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5BX_NFLVERSE_2010_2019_SOURCE_COVERAGE_PIPELINE_FEASIBILITY.md`
- `docs/outcome_probability/BUILD_SPRINT_5BY_2019_2015_2016_SOURCE_REGISTRATION_AUDIT.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

No local exports were created in 5CB.

## 2. Registration Decision

| Source season | Intended future use | Source-registration verdict | Modeling approval |
| ---: | --- | --- | --- |
| 2013 | completed prior season for future 2014 target rows | YELLOW | not approved |
| 2014 | completed prior season for future 2015 target rows | YELLOW | not approved |

5CB is YELLOW because both 2013 and 2014 have unresolved missing `position` values on offensive rows. Those rows include QB/RB/WR/TE-relevant statistical activity, and the same local `player_stats.csv` file does not provide a nonblank position for the affected `player_id` values elsewhere. The missing positions are therefore not safely repairable from the registered source evidence in this sprint.

Because 5CB is YELLOW, the autorun must stop before 5CC. No 2014-2015 feature/label rebuild is approved.

## 3. Source Coverage

Source path:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

| Source season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate key extra rows | Missing player ID | Missing team/recent_team | Missing position |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 2013 | 5231 | 5022 | 1-17 | 591 | 0 | 0 | 0 | 25 |
| 2014 | 5350 | 5129 | 1-17 | 589 | 0 | 0 | 0 | 20 |

Duplicate key definition:

`player_id + season + week + season_type`

Duplicate-key result: pass.

Identity/team result: pass.

Position result: fail for GREEN registration; YELLOW overall because the issue is contained and documented, but unresolved.

## 4. QB/RB/WR/TE Row Counts

Rows with explicit modeled positions:

| Source season | QB rows | RB rows | WR rows | TE rows |
| ---: | ---: | ---: | ---: | ---: |
| 2013 | 609 | 1320 | 2002 | 988 |
| 2014 | 619 | 1404 | 2050 | 1034 |

These counts exclude rows where `position` is blank. The blank-position rows include offensive touches/targets and therefore cannot be ignored for future source registration without a repair policy.

## 5. Missing-Position Blocker

Affected unique player IDs found in blank-position rows:

| Source season | Player ID | Display name | Teams seen in blank rows | Evidence issue |
| ---: | --- | --- | --- | --- |
| 2013 | `00-0027567` | Steve Maneri | CHI | blank `position`, blank `position_group`, target activity |
| 2013 | `00-0028543` | Jeff Maehl | PHI | blank `position`, blank `position_group`, receiving activity |
| 2013 | `00-0029675` | Trent Richardson | CLE/IND | blank `position`, blank `position_group`, rushing/receiving activity |
| 2014 | `00-0027567` | Steve Maneri | NE | blank `position`, blank `position_group`, target activity |
| 2014 | `00-0028543` | Jeff Maehl | PHI | blank `position`, blank `position_group`, receiving activity |
| 2014 | `00-0029675` | Trent Richardson | IND | blank `position`, blank `position_group`, rushing/receiving activity |

The same local `player_stats.csv` source does not contain nonblank position evidence for these player IDs in other rows. Position repair may be possible from another approved identity/roster source, but that source is not registered for this sprint. Therefore, 2013 and 2014 are not GREEN for completed-prior-source use yet.

## 6. Field Availability

| Source season | Passing fields | Rushing fields | Receiving fields | Rush first downs missing | Receiving first downs missing | Fumble-lost components | `special_teams_tds` |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 2013 | available | available | available | 0 | 0 | available | available |
| 2014 | available | available | available | 0 | 0 | available | available |

Passing, rushing, receiving, first-down, and fumble-lost fields are structurally available and complete for the audited rows. This is not enough to clear GREEN while position evidence remains unresolved.

## 7. Return-Stat Gap

The local source includes `special_teams_tds`, but it does not include granular return yards, kick return yards, punt return yards, return TDs, kick return TDs, or punt return TDs.

Registration handling:

- exact return-yard scoring remains unavailable from `player_stats.csv` alone;
- special teams TD evidence is available but not granular by return type;
- any future exact return scoring claim would need a separate approved source.

This return-stat gap is documented but is not the primary 5CB blocker. The primary blocker is unresolved position missingness.

## 8. Forbidden And Quarantined Fields

Forbidden or quarantined from prediction features:

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
- same-season target final stats as preseason features
- label supplement sources as prediction features

Any future repair or row-generation sprint must enforce a positive allowlist and rerun a forbidden-field scan.

## 9. Release Stance

5CB does not approve feature/label rebuild rows.

5CB does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 10. Required Next Step

Recommended next safe sprint: Sprint 5CC-R - 2013-2014 position repair feasibility audit using an explicitly approved local identity/roster source.

That sprint should determine whether the blank-position player IDs can be repaired from a source-safe local roster/player registry without introducing leakage, market data, projections, rankings, or manual app-facing assumptions. Only after that repair audit passes should a 2014-2015 local-only feature/label rebuild be reconsidered.

## 11. Checks

Checks run:

- local CSV inventory completed with no downloads and no package installation
- `git diff --check` passed

Ruff was not required because no tracked Python file changed in 5CB. Pytest was not required because no tracked code or test file changed in 5CB.
