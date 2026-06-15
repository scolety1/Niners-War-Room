# Sprint 5CG: Audit 5CF 2012-2013 Historical Feature Label Package

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_INTERNAL_ONLY_AUDIT_RELEASE_BLOCKED`

Sprint type: `ADVERSARIAL_AUDIT_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CG audits the Sprint 5CF local-only 2012-2013 historical feature/label rebuild package. This audit did not train models, generate probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, edit `data/`, or create promoted artifacts.

Audited tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5CF_LOCAL_ONLY_2012_2013_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `scripts/outcome_probability/build_sprint_5cf_2012_2013_historical_feature_label_rebuild.py`

Audited local-only export:

`local_exports/outcome_probability/sprint_5cf_2012_2013_historical_feature_label_rebuild/`

Audited commit:

`3021b7d Build 5CF local historical feature label package`

## 2. Local-Only Audit Export

Created local-only audit export:

`local_exports/outcome_probability/sprint_5cg_audit_2012_2013_historical_feature_label_package/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5cg.json` | audit verdict, counts, release-blocker flags | no |
| `audit_checks.csv` | pass/fail audit checks | no |
| `row_counts_by_target_season_position.csv` | row counts by target season and position | no |
| `blocked_reason_counts.csv` | blocked-row reason counts | no |
| `repair_overlay_counts.csv` | 5CE-R2 repair overlay row counts | no |
| `README_SPRINT_5CG.md` | local audit summary | no |

All 5CG audit exports are internal-only and not app-readable.

## 3. Row Count Audit

Row count result: pass.

| Target season | QB | RB | WR | TE | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2012 | 51 | 97 | 144 | 83 | 375 |
| 2013 | 53 | 102 | 143 | 81 | 379 |
| Total | 104 | 199 | 287 | 164 | 754 |

Expected 2012 rows: 375. Actual: 375.

Expected 2013 rows: 379. Actual: 379.

Expected total rows: 754. Actual feature rows: 754. Actual label rows: 754.

## 4. Blocked Row Audit

Blocked-row result: pass.

| Block reason | Rows |
| --- | ---: |
| `blocked_missing_label` | 279 |

Expected blocked rows: 279. Actual: 279.

Every blocked row is `blocked_missing_label`.

No other block reasons exist.

Blocked rows remain local-only, not app-readable, unscored, unsorted, and unpromoted.

## 5. 5CE-R2 Repair Overlay Audit

Repair overlay result: pass.

| Player ID | Player | Position | Expected rows | Actual rows |
| --- | --- | --- | ---: | ---: |
| `00-0027567` | Steve Maneri | TE | 7 | 7 |
| `00-0028543` | Jeff Maehl | WR | 1 | 1 |
| `00-0029675` | Trent Richardson | RB | 15 | 15 |
| Total |  |  | 23 | 23 |

The overlay is limited to the approved 5CE-R2 mapping and is audit-time only. Raw `player_stats.csv` was not modified.

## 6. Duplicate Keys

Duplicate-key result: pass.

| Key type | Season scope | Duplicate extra rows | Status |
| --- | --- | ---: | --- |
| source_player_week | 2011 | 0 | pass |
| source_player_week | 2012 | 0 | pass |
| feature_snapshot | 2012-2013 package | 0 | pass |
| label_row | 2012-2013 package | 0 | pass |

## 7. Identity, Team, And Position

Identity/team/position result: pass.

| Row family | Season | Rows checked | Missing player ID | Missing player display name | Missing team | Missing position | Missing position group | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| feature_source | 2011 | 5006 | 0 | 0 | 0 | 0 | 0 | pass |
| feature_source | 2012 | 5025 | 0 | 0 | 0 | 0 | 0 | pass |
| label_source | 2012 | 5025 | 0 | 0 | 0 | 0 | 0 | pass |
| label_source | 2013 | 4919 | 0 | 0 | 0 | 0 | 0 | pass |

Historical blank `player_name` values are covered by complete `player_display_name` values. No app-facing identity bridge is approved by this sprint.

## 8. First-Down Completeness

First-down completeness result: pass.

| Row family | Season | Rows checked | Missing rushing first downs | Missing receiving first downs | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| feature_source | 2011 | 5006 | 0 | 0 | pass |
| feature_source | 2012 | 5025 | 0 | 0 | pass |
| label_source | 2012 | 5025 | 0 | 0 | pass |
| label_source | 2013 | 4919 | 0 | 0 | pass |

## 9. Forbidden-Field Quarantine

Forbidden-field quarantine result: pass.

The audit confirmed quarantined fields are not used in features, including:

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

The package does not use ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, same-season final stats as preseason features, or label supplement sources as prediction features.

## 10. Output Quarantine

Output quarantine result: pass.

The 5CF package remains local-only under:

`local_exports/outcome_probability/sprint_5cf_2012_2013_historical_feature_label_rebuild/`

The 5CG audit export remains local-only under:

`local_exports/outcome_probability/sprint_5cg_audit_2012_2013_historical_feature_label_package/`

No app-readable production artifact was created.

No exact percentages were created.

No coarse bands were created.

No modeling was performed.

No app wiring was created.

No rankings/sorting changes were made.

No hidden sort keys were created.

No promoted artifacts were created.

## 11. Release Stance

5CF remains suitable only as a local historical feature/label package. It is not production ranking input, not display input, not a model release, and not an app-readable probability or band artifact.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but 5CG creates no app-readable status table.

## 12. Verdict

5CG audit verdict: GREEN for internal audit review.

5CG does not approve modeling, probabilities, coarse bands, app display, rankings/sorting, hidden sort keys, or promoted artifacts.

## 13. Recommended Next Safe Sprint

Recommended next safe sprint: Outcome HQ review and, if approved, commit the 5CG audit report only. After that, the next research direction should remain gated by HQ and should not promote any local historical package into production use without a separate release-path decision.

## 14. Checks

Checks run:

- local CSV audit of the 5CF package completed with no downloads and no package installation
- `git diff --check` passed

No Python files changed in 5CG, so `python -m py_compile` and Ruff were not required. Pytest was not required because no code or tests changed.
