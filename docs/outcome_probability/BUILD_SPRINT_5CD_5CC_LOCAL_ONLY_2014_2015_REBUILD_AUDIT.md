# Sprint 5CD: 5CC Local-Only 2014-2015 Rebuild Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_INTERNAL_ONLY_AUDIT_RELEASE_BLOCKED`

Sprint type: `ADVERSARIAL_AUDIT_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CD audits the Sprint 5CC local-only 2014-2015 historical feature/label rebuild package. This audit did not train models, generate probabilities, create coarse bands, create app-readable status/probability/band outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, edit raw data, or create promoted artifacts.

Audited package:

`local_exports/outcome_probability/sprint_5cc_2014_2015_historical_feature_label_rebuild/`

Audited commit:

`72bad43e418928a6b220d000dcece7e1d1a4820c`

## 2. Artifact Quarantine

Artifact quarantine result: pass.

The 5CC package exists only under `local_exports/outcome_probability/sprint_5cc_2014_2015_historical_feature_label_rebuild/`. Metadata records `output_scope=internal_only_not_app_readable`, `app_readable_output_created=false`, `model_training_performed=false`, `probabilities_generated=false`, `ranking_sorting_changed=false`, and `promoted_artifacts_created=false`.

No app path, player-card path, ranking/sorting path, release-service path, app-loader path, hidden sort key, promoted artifact path, or app-readable probability/band/status table was created.

5CC tracked commit scope was limited to:

- `docs/outcome_probability/BUILD_SPRINT_5CC_LOCAL_ONLY_2014_2015_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `scripts/outcome_probability/build_sprint_5cc_2014_2015_historical_feature_label_rebuild.py`

## 3. Target/Source Split Discipline

Split discipline result: pass.

| Target season | Feature source season | Label source season | Audit result |
| ---: | ---: | ---: | --- |
| 2014 | completed 2013 regular season only, with approved 5CC-R2 position repair overlay | final 2014 regular-season stats only | pass |
| 2015 | completed 2014 regular season only, with approved 5CC-R2 position repair overlay | final 2015 regular-season stats only | pass |

Same-season final stats are labels only. They are not used as preseason prediction features.

All 760 emitted legality rows have `legality_status=pass`.

## 4. Approved Position Repair Overlay

Repair overlay result: pass.

5CC used the approved deterministic 5CC-R2 overlay only for blank `position` or `position_group` offensive rows in 2013-2014. Raw `player_stats.csv` was not modified.

| Player ID | Player | Repair position | Repaired rows |
| --- | --- | --- | ---: |
| `00-0027567` | Steve Maneri | TE | 3 |
| `00-0028543` | Jeff Maehl | WR | 9 |
| `00-0029675` | Trent Richardson | RB | 33 |
| Total |  |  | 45 |

The repaired position is used only for source registration and normal legal row eligibility, not as a new model signal.

## 5. Row Generation Evidence

5CC generated local-only historical rows only:

| Target season | Attempted rows | Feature snapshots | Label rows | Blocked rows | Primary blocker |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2014 | 515 | 373 | 373 | 142 | `blocked_missing_label` |
| 2015 | 521 | 387 | 387 | 134 | `blocked_missing_label` |
| Total | 1036 | 760 | 760 | 276 | `blocked_missing_label` |

Blocked rows remain local-only, not app-readable, and unscored.

## 6. NWR Scoring Reconstruction

NWR scoring reconstruction result: pass.

Labels were reconstructed from source-safe target-season raw components:

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

Imported fantasy totals are quarantined and not copied into features or labels.

## 7. First Downs, Identity, And Duplicate Keys

First-down completeness result: pass.

| Row family | Season | Rows checked | Missing rushing first downs | Missing receiving first downs | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| feature_source | 2013 | 4944 | 0 | 0 | pass |
| feature_source | 2014 | 5127 | 0 | 0 | pass |
| label_source | 2014 | 5127 | 0 | 0 | pass |
| label_source | 2015 | 5109 | 0 | 0 | pass |

Duplicate-key result: pass.

| Key type | Season scope | Duplicate extra rows | Status |
| --- | --- | ---: | --- |
| source_player_week | 2013 | 0 | pass |
| source_player_week | 2014 | 0 | pass |
| feature_snapshot | 2014-2015 package | 0 | pass |
| label_row | 2014-2015 package | 0 | pass |

Identity/team/position result: pass.

| Row family | Season | Rows checked | Missing player ID | Missing player display name | Missing team | Missing position | Missing position group | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| feature_source | 2013 | 4944 | 0 | 0 | 0 | 0 | 0 | pass |
| feature_source | 2014 | 5127 | 0 | 0 | 0 | 0 | 0 | pass |
| label_source | 2014 | 5127 | 0 | 0 | 0 | 0 | 0 | pass |
| label_source | 2015 | 5109 | 0 | 0 | 0 | 0 | 0 | pass |

## 8. Forbidden-Field Quarantine

Forbidden-field scan result: pass.

The 5CC positive allowlist excludes forbidden/quarantined contexts. The local source contains several quarantined fields, all marked `used_in_features=no`, including:

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

The package did not use ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, same-season target stats as preseason features, or label supplement sources as prediction features.

## 9. Release/Display Stance

Release/display stance: blocked.

The 5CC package records these blockers:

- modeling: `blocked`
- exact percentages: `blocked`
- coarse bands: `blocked`
- app wiring: `blocked`
- rankings/sorting: `blocked`
- hidden sort keys: `blocked`
- promoted artifacts: `blocked`

Existing status-only Outcome Model Status copy remains safe, but 5CD creates no app-readable status table and approves no numeric display.

## 10. Verdict

5CD audit verdict: GREEN for internal audit commit.

5CC remains blocked for modeling, exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, and promoted artifacts.

## 11. Recommended Next Safe Sprint

Recommended next safe sprint: Sprint 5CE - 2011-2012 source registration audit.

Proceed only if 5CD is committed and 5CE source registration is GREEN. If either 2011 or 2012 has unresolved blockers, stop before any 2012-2013 rebuild.

## 12. Checks

Checks run:

- `git diff --check` passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5cc_2014_2015_historical_feature_label_rebuild.py` passed
