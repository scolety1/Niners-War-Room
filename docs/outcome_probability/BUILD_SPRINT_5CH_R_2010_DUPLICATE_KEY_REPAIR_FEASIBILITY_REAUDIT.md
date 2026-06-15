# Sprint 5CH-R: 2010 Duplicate-Key Repair Feasibility And Re-Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_DETERMINISTIC_DUPLICATE_REPAIR_FEASIBLE_NO_REBUILD`

Sprint type: `DUPLICATE_KEY_REPAIR_FEASIBILITY_NO_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5CH-R audits whether the Matthew Stafford 2010 week 8 duplicate `player_id + season + week + season_type` key can be repaired deterministically using only local source evidence and without editing raw data. This sprint does not build the 2010-2011 feature/label package, train models, generate probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, edit `data/`, or create promoted artifacts.

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5CH_EARLIEST_HISTORICAL_BOUNDARY_SOURCE_FEASIBILITY_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5CE_R2_2011_2012_POSITION_REPAIR_REAUDIT.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

No internet lookup was performed. No package installation was performed. No manual guessing was used.

## 2. Local-Only Audit Export

Created local-only audit export:

`local_exports/outcome_probability/sprint_5ch_r_2010_duplicate_key_repair_feasibility/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5ch_r.json` | run metadata, verdict, release blockers | no |
| `matthew_stafford_2010_week8_duplicate_rows.csv` | duplicate row inspection | no |
| `matthew_stafford_2010_week8_differing_fields.csv` | field-level differences between duplicate rows | no |
| `proposed_duplicate_repair_excluded_rows.csv` | rows excluded by the proposed audit-time overlay | no |
| `source_registration_summary_before_overlay.csv` | 2009-2011 source checks before duplicate overlay | no |
| `source_registration_summary_after_overlay.csv` | 2009-2011 source checks after duplicate overlay | no |
| `forbidden_quarantine_scan.csv` | forbidden/quarantined source field scan | no |
| `return_stat_limitations.csv` | return-stat availability limits | no |
| `audit_checks.csv` | pass/fail audit checks | no |
| `README_SPRINT_5CH_R.md` | local-only audit summary | no |

All outputs are internal-only and not app-readable.

## 3. Duplicate Key Inspected

Exact duplicate key:

| Player ID | Player | Season | Week | Season type | Team | Position |
| --- | --- | ---: | ---: | --- | --- | --- |
| `00-0026498` | Matthew Stafford | 2010 | 8 | REG | DET | QB |

Two rows exist for this exact key. They are not identical.

## 4. Duplicate Row Classification

| Duplicate row | Source-safe raw activity | Fantasy totals | Repair action |
| ---: | --- | --- | --- |
| 1 | `completions`, `attempts`, `passing_yards`, `passing_tds`, `interceptions` | `fantasy_points=22.48`, `fantasy_points_ppr=22.48` | keep source-safe activity row |
| 2 | none from approved NWR raw activity fields | `fantasy_points=2`, `fantasy_points_ppr=2` | exclude duplicate supplemental/noise row |

The second row also carries `passing_2pt_conversions=1`, but two-point conversion fields are not approved source-safe features or labels in the existing NWR reconstruction contract for these historical packages. Because the row has zero approved passing/rushing/receiving/first-down/fumble activity and relies on non-allowlisted or quarantined scoring context, it is not safe to keep as an additional source row for the local feature/label package.

## 5. Differing Fields

Differing fields between the duplicate rows:

| Field | Kept source-safe activity row | Excluded supplemental row |
| --- | --- | --- |
| `completions` | 26 | 0 |
| `attempts` | 45 | 0 |
| `passing_yards` | 212 | 0 |
| `passing_tds` | 4 | 0 |
| `interceptions` | 1 | 0 |
| `sacks` | 1 | 0 |
| `sack_yards` | 10 | 0 |
| `passing_air_yards` | 317 | 0 |
| `passing_yards_after_catch` | 102 | 0 |
| `passing_first_downs` | 10 | 0 |
| `passing_epa` | -4.70635456684977 | blank |
| `passing_2pt_conversions` | 0 | 1 |
| `pacr` | 0.668769716088328 | blank |
| `dakota` | 0.00144771406697761 | blank |
| `fantasy_points` | 22.48 | 2 |
| `fantasy_points_ppr` | 22.48 | 2 |

The kept row contains the complete approved source-safe raw passing line for the player-week. The excluded row is not a valid additional source-safe player-week line for the existing NWR feature/label rebuild policy.

## 6. Proposed Deterministic Repair Rule

Recommended audit/build-time overlay for a future 2010-2011 package:

1. Identify rows with exact key `player_id=00-0026498`, `season=2010`, `week=8`, `season_type=REG`.
2. Keep the row with non-zero approved source-safe raw activity fields.
3. Exclude the row with zero approved source-safe raw activity fields.
4. Do not use `fantasy_points`, `fantasy_points_ppr`, EPA, PACR, Dakota, or `passing_2pt_conversions` as prediction features or labels.
5. Emit a local-only duplicate repair audit showing the kept/excluded row and field differences.
6. Do not modify raw `player_stats.csv`.

This repair is deterministic and source-safe. It does not require manual guessing.

## 7. Source Registration Re-Audit After Proposed Overlay

| Season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate extra rows | Blank offensive position rows | Verdict |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2009 | 5242 | 5035 | 1-17 | 563 | 0 | 0 | GREEN |
| 2010 | 5203 | 4987 | 1-17 | 580 | 0 | 0 | GREEN |
| 2011 | 5301 | 5091 | 1-17 | 586 | 0 | 0 | GREEN |

2009 coverage result: GREEN.

2010 source registration result after proposed duplicate overlay: GREEN.

2011 source registration result after 5CE-R2 position overlay: GREEN.

## 8. Identity, Team, Position, And First Downs

Identity/team/position result: pass.

| Season | Missing player ID | Missing team | Missing position | Missing position group | Result |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2009 | 0 | 0 | 0 | 0 | pass |
| 2010 after duplicate overlay | 0 | 0 | 0 | 0 | pass |
| 2011 after 5CE-R2 overlay | 0 | 0 | 0 | 0 | pass |

First-down completeness result: pass.

| Season | Modeled REG rows | Missing rushing first downs | Missing receiving first downs | Result |
| ---: | ---: | ---: | ---: | --- |
| 2009 | 4712 | 0 | 0 | pass |
| 2010 after duplicate overlay | 4684 | 0 | 0 | pass |
| 2011 after 5CE-R2 overlay | 4808 | 0 | 0 | pass |

## 9. Forbidden-Field Quarantine

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

## 10. Return-Stat Limitation

Return-stat limitation remains unchanged.

| Field | Available in local `player_stats.csv`? | Approved for source-safe NWR reconstruction? |
| --- | --- | --- |
| `special_teams_tds` | yes | no |
| `return_yards` | no | no |
| `return_tds` | no | no |
| `punt_return_yards` | no | no |
| `kickoff_return_yards` | no | no |
| `punt_return_tds` | no | no |
| `kickoff_return_tds` | no | no |

Granular return yards and return touchdowns remain unavailable from `player_stats.csv` alone. Return scoring remains excluded unless a later sprint registers and audits a legal granular source.

## 11. Recommendation

5CH-R recommendation: GREEN.

The Matthew Stafford 2010 week 8 duplicate repair is deterministic, source-safe, and narrow enough for a future build-time overlay. After the proposed overlay, 2009, 2010, and 2011 source registration are GREEN.

The next local-only rebuild package may be proposed as a 2010-2011 historical feature/label rebuild package, but only after HQ explicitly approves that sprint. This sprint does not build it.

## 12. Release Stance

5CH-R does not build the 2010-2011 feature/label package.

5CH-R does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 13. Checks

Checks run:

- required repo/branch/status/log preflight passed
- local duplicate-key audit completed with no downloads and no package installation
- `git diff --check` passed

No Python files were changed in 5CH-R, so `python -m py_compile` and Ruff were not required. Pytest was not required because no code or tests changed.
