# Sprint 5CD: Adversarial Audit of 5CC Local-Only 2014-2015 Historical Feature/Label Rebuild

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN`

Audit type: `LOCAL_ONLY_ADVERSARIAL_AUDIT_NO_MODELING_NO_RELEASE`

## Files Inspected

Tracked 5CC package files:

- `docs/outcome_probability/BUILD_SPRINT_5CC_LOCAL_ONLY_2014_2015_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `scripts/outcome_probability/build_sprint_5cc_2014_2015_historical_feature_label_rebuild.py`

Local-only exports inspected:

- `local_exports/outcome_probability/sprint_5cc_2014_2015_historical_feature_label_rebuild/`

No 5CD audit script was needed.

## Row-Count Verification

GREEN.

Feature snapshot and label rows match the 5CC claimed counts:

| Target season | QB | RB | WR | TE | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2014 | 58 | 97 | 137 | 81 | 373 |
| 2015 | 60 | 102 | 138 | 87 | 387 |
| Total | 118 | 199 | 275 | 168 | 760 |

Blocked rows:

| Target season | Blocked rows | Block reason |
| ---: | ---: | --- |
| 2014 | 142 | `blocked_missing_label` |
| 2015 | 134 | `blocked_missing_label` |
| Total | 276 | `blocked_missing_label` |

## Leakage Audit

GREEN.

Target/source mapping verified:

| Target season | Feature source season | Label source season | Result |
| ---: | ---: | ---: | --- |
| 2014 | 2013 | 2014 | pass |
| 2015 | 2014 | 2015 | pass |

All emitted legality rows pass:

- `source_season_strictly_before_target=yes`
- `same_season_final_stats_as_features=no`
- `label_source_as_prediction_feature=no`
- `fantasy_totals_used=no`
- `legality_status=pass`

No same-season target labels were used as prediction features. No future-season leakage was detected.

## Forbidden-Field Audit

GREEN.

No forbidden or quarantined field is used in feature exports. Excluded/quarantined families include fantasy totals, EPA, WOPR/RACR/PACR/Dakota/target-share fields, ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire fields, prior fantasy draft history, and legacy `private_score`.

## Blocked-Row Audit

GREEN.

Blocked rows are correctly quarantined:

- blocked rows: `276`
- blocked reason: `blocked_missing_label`
- blocked rows intersecting emitted label keys: `0`

No `blocked_missing_label` row is silently emitted as a valid label row.

## Identity And Duplicate Audit

GREEN.

Duplicate-key audit:

- source player-week 2013 duplicate extra rows: `0`
- source player-week 2014 duplicate extra rows: `0`
- feature snapshot duplicate extra rows: `0`
- label row duplicate extra rows: `0`

Identity/team/position audit:

- missing player ID: `0`
- missing player display name: `0`
- missing team: `0`
- missing position: `0`
- missing position group: `0`

The approved 5CC-R2 repair overlay is limited to:

| Player ID | Player | Repair position | Repaired rows |
| --- | --- | --- | ---: |
| `00-0027567` | Steve Maneri | TE | 3 |
| `00-0028543` | Jeff Maehl | WR | 9 |
| `00-0029675` | Trent Richardson | RB | 33 |
| Total |  |  | 45 |

No duplicate or cross-player contamination was detected from the overlay.

## First-Down Audit

GREEN.

First-down completeness is real and not filled by illegal fallback:

| Row family | Season | Missing rushing first downs | Missing receiving first downs | Status |
| --- | ---: | ---: | ---: | --- |
| feature source | 2013 | 0 | 0 | pass |
| feature source | 2014 | 0 | 0 | pass |
| label source | 2014 | 0 | 0 | pass |
| label source | 2015 | 0 | 0 | pass |

## Scoring Reconstruction Audit

GREEN.

Independent reconstruction from source-safe regular-season raw components matched all `760` emitted label rows.

Recomputed components:

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

Mismatch count: `0`.

This verifies NWR scoring reconstruction uses source-safe raw components, not copied fantasy totals.

## Output Quarantine Audit

GREEN.

The package is local-only under:

`local_exports/outcome_probability/sprint_5cc_2014_2015_historical_feature_label_rebuild/`

Metadata confirms:

- `output_scope=internal_only_not_app_readable`
- `app_release_status=blocked_not_app_readable`
- `app_readable_output_created=false`
- `model_training_performed=false`
- `probabilities_generated=false`
- `ranking_sorting_changed=false`
- `promoted_artifacts_created=false`

Feature rows and label rows keep:

- `app_readable=no`
- `sort_allowed=no`
- `ranking_use_allowed=no`

Generated outputs are not promoted and are not consumed by ranking, sorting, modeling, or app surfaces.

## Release Blockers

GREEN.

The following remain blocked:

- modeling
- exact percentages
- coarse bands
- app wiring
- rankings/sorting
- hidden sort keys
- promoted artifacts

Sprint 5CD does not unblock any of these.

## Commit Guidance

5CC is safe for tracked commit from this 5CD audit perspective.

5CC and 5CD are preferably committed separately for traceability. If HQ requires an atomic reviewed package, committing tracked 5CC and tracked 5CD together is also safe, provided `data/` and `local_exports/` are excluded.

## Exact Next Safe Step

Outcome HQ reviews this 5CD audit doc plus the 5CC package. If HQ approves, commit the tracked 5CD audit doc only, excluding `data/`, `local_exports/`, and unrelated docs.

Do not model, train, create exact percentages, create coarse bands, wire app output, create rankings/sorting, or promote artifacts.
