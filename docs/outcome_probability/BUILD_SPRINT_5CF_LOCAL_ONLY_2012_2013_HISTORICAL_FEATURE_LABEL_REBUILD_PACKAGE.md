# Sprint 5CF: Local-Only 2012-2013 Historical Feature Label Rebuild Package

Outcome lane: veteran outcome probability column path only

Verdict: `LOCAL_ONLY_2012_2013_FEATURE_LABEL_ROWS_GENERATED_MODELING_BLOCKED`

Sprint type: `LOCAL_ONLY_ROW_GENERATION_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CF generated a local-only 2012-2013 historical feature and label rebuild package after 5CE-R2 made 2011 and 2012 source registration GREEN with a deterministic audit-time position repair overlay. This sprint did not train models, generate probabilities, create coarse bands, create app-readable status/probability/band outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, edit raw data, or create promoted artifacts.

Evidence used:

- `docs/outcome_probability/BUILD_SPRINT_5CE_2011_2012_SOURCE_REGISTRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5CE_R_2011_2012_POSITION_REPAIR_FEASIBILITY_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5CE_R2_2011_2012_POSITION_REPAIR_REAUDIT.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Generator:

- `scripts/outcome_probability/build_sprint_5cf_2012_2013_historical_feature_label_rebuild.py`

## 2. Local-Only Package

Package path:

`local_exports/outcome_probability/sprint_5cf_2012_2013_historical_feature_label_rebuild/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5cf.json` | run metadata, source path, commit, repair overlay, gate status | no |
| `historical_2012_2013_feature_snapshots.csv` | completed prior-season feature snapshots | no |
| `historical_2012_2013_outcome_labels.csv` | target-season labels rebuilt from source-safe NWR components | no |
| `blocked_historical_2012_2013_rows.csv` | blocked/unscored candidate source rows | no |
| `historical_2012_2013_trainability_report.csv` | emitted/blocked row counts and blocker reasons | no |
| `historical_2012_2013_feature_missingness.csv` | feature missingness by target season | no |
| `historical_2012_2013_label_support.csv` | threshold/tier support counts only | no |
| `historical_2012_2013_legality_audit.csv` | completed-prior-season and leakage checks | no |
| `historical_2012_2013_forbidden_feature_scan.csv` | positive allowlist and forbidden/quarantine scan | no |
| `historical_2012_2013_identity_team_position_audit.csv` | identity, team, and position coverage checks | no |
| `historical_2012_2013_duplicate_key_audit.csv` | player-week and target-row uniqueness checks | no |
| `historical_2012_2013_population_policy_audit.csv` | veteran, rookie, kicker, blocked, and current-pool policy checks | no |
| `historical_2012_2013_first_down_completeness.csv` | rushing/receiving first-down completeness checks | no |
| `position_repair_overlay_audit.csv` | rows receiving the approved 5CE-R2 repair overlay | no |
| `artifact_quarantine_audit.csv` | output quarantine and release-path isolation checks | no |
| `release_blockers.csv` | explicit blockers for modeling, display, sorting, and promotion | no |
| `README_SPRINT_5CF.md` | local package summary and release stance | no |

All generated outputs are marked `internal_only_not_app_readable`.

## 3. Target And Source Mapping

| Target season | Feature source season | Label source season | Result |
| ---: | ---: | ---: | --- |
| 2012 | completed 2011 regular season only, with approved 5CE-R2 position repair overlay | final 2012 regular-season stats only | generated |
| 2013 | completed 2012 regular season only, with approved 5CE-R2 position repair overlay | final 2013 regular-season stats only | generated |

Same-season final target stats were used only as labels. They were not used as preseason prediction features.

## 4. Deterministic Position Repair Overlay

The 5CF generator applies the approved 5CE-R2 overlay at audit time only. Raw `player_stats.csv` is not modified.

Approved mapping:

| Player ID | Player | Repair position | Repaired rows |
| --- | --- | --- | ---: |
| `00-0027567` | Steve Maneri | TE | 7 |
| `00-0028543` | Jeff Maehl | WR | 1 |
| `00-0029675` | Trent Richardson | RB | 15 |
| Total |  |  | 23 |

The overlay is limited to 2011-2012 rows where the player ID is in the approved mapping, `position` or `position_group` is blank, and offensive activity is present. The repaired position is used only for source registration and normal legal position eligibility, not as a new model signal.

## 5. Generated Row Counts

Overall generation:

| Target season | Attempted rows | Feature snapshots | Label rows | Blocked rows | Primary blocker |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2012 | 513 | 375 | 375 | 138 | `blocked_missing_label` |
| 2013 | 520 | 379 | 379 | 141 | `blocked_missing_label` |
| Total | 1033 | 754 | 754 | 279 | `blocked_missing_label` |

Generated label rows by target season and position:

| Target season | QB | RB | WR | TE | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2012 | 51 | 97 | 144 | 83 | 375 |
| 2013 | 53 | 102 | 143 | 81 | 379 |
| Total | 104 | 199 | 287 | 164 | 754 |

Blocked rows remain local-only, not app-readable, and unscored. All blocked rows were blocked because no matching target-season label row was available:

| Target season | Block reason | Blocked rows |
| ---: | --- | ---: |
| 2012 | `blocked_missing_label` | 138 |
| 2013 | `blocked_missing_label` | 141 |

## 6. NWR Scoring Reconstruction

Labels were reconstructed from source-safe target-season components only:

- passing yards divided by 30
- passing touchdowns times 3
- interceptions times -1
- rushing yards times 0.1
- rushing touchdowns times 4
- rushing first downs times 0.4
- receiving yards times 0.1
- receiving touchdowns times 4
- receiving first downs times 0.4
- rushing, receiving, and sack fumbles lost times -1

The package did not copy fantasy totals, projections, rankings, ADP, market values, trade values, RotoWire fields, prior fantasy draft history, or legacy `private_score` into features or labels. Return-yard scoring remains excluded because granular return yards and granular return TD fields are not available from the registered `player_stats.csv` source.

## 7. First-Down Completeness

First-down completeness passed for both feature-source and label-source seasons:

| Row family | Season | Rows checked | Missing rushing first downs | Missing receiving first downs | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| feature_source | 2011 | 5006 | 0 | 0 | pass |
| feature_source | 2012 | 5025 | 0 | 0 | pass |
| label_source | 2012 | 5025 | 0 | 0 | pass |
| label_source | 2013 | 4919 | 0 | 0 | pass |

## 8. Duplicate Keys And Identity

Duplicate-key checks passed:

| Key type | Season scope | Duplicate extra rows | Status |
| --- | --- | ---: | --- |
| source_player_week | 2011 | 0 | pass |
| source_player_week | 2012 | 0 | pass |
| feature_snapshot | 2012-2013 package | 0 | pass |
| label_row | 2012-2013 package | 0 | pass |

Identity/team/position coverage:

| Row family | Season | Rows checked | Missing player ID | Missing player display name | Missing team | Missing position | Missing position group | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| feature_source | 2011 | 5006 | 0 | 0 | 0 | 0 | 0 | pass |
| feature_source | 2012 | 5025 | 0 | 0 | 0 | 0 | 0 | pass |
| label_source | 2012 | 5025 | 0 | 0 | 0 | 0 | 0 | pass |
| label_source | 2013 | 4919 | 0 | 0 | 0 | 0 | 0 | pass |

Historical nuance: the local source has blank `player_name` values on some rows, but `player_display_name`, `player_id`, team, position, and position group are complete after the 5CE-R2 overlay. The package uses the display-name fallback and does not require an app-facing identity bridge in this sprint.

## 9. Forbidden-Field And Leakage Scan

Forbidden-field scan result: pass.

No feature row uses a forbidden or quarantined field. The positive allowlist excludes:

- ADP
- public rankings
- projections
- consensus
- market values
- trade values/calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- fantasy totals
- EPA
- WOPR/RACR/PACR/Dakota/target-share style fields
- same-season target stats as preseason features
- label supplement sources as prediction features

Leakage-control result: pass.

All 754 emitted rows have `legality_status=pass`.

## 10. Population Policy

The package includes QB/RB/WR/TE only. Rookies are excluded from veteran heads by requiring a completed prior-season source row before a target-season row can be emitted. Kickers are not applicable and were not modeled. Current 2026 pool rows were not generated or scored.

## 11. Artifact Quarantine And Release Blockers

Artifact quarantine result: pass.

The package is local-only under `local_exports/outcome_probability/sprint_5cf_2012_2013_historical_feature_label_rebuild/`. No app path, release-service path, ranking/sorting path, hidden sort key, promoted artifact path, or app-readable probability/band/status table was created.

The package records these blockers:

- modeling: `blocked`
- exact percentages: `blocked`
- coarse bands: `blocked`
- app wiring: `blocked`
- rankings/sorting: `blocked`
- hidden sort keys: `blocked`
- promoted artifacts: `blocked`

## 12. Release Stance

Sprint 5CF creates historical rows only. It does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting usage and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but no new app-readable status table was created in this sprint.

## 13. Recommended Next Safe Sprint

Recommended next safe sprint: Sprint 5CG - adversarial audit of the 5CF local-only 2012-2013 historical feature and label rebuild package.

The audit should independently verify target/source mapping, 5CE-R2 repair overlay limits, leakage controls, source-safe NWR reconstruction, first-down completeness, duplicate keys, identity fallback handling, forbidden-field quarantine, artifact quarantine, and release blockers.

## 14. Checks

Checks run:

- `python scripts\outcome_probability\build_sprint_5cf_2012_2013_historical_feature_label_rebuild.py` passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5cf_2012_2013_historical_feature_label_rebuild.py` passed
- `git diff --check` passed

Ruff was not required beyond availability because no lint-only gate was requested by HQ for this restart. Pytest was not required because no tests changed.
