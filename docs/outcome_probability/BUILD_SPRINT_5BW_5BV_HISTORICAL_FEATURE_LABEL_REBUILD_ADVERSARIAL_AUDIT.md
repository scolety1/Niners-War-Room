# Sprint 5BW: 5BV Historical Feature Label Rebuild Adversarial Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_FOR_INTERNAL_AUDIT_COMMIT_RELEASE_DISPLAY_BLOCKED`

Audited 5BV commit: `ad7c6fb`

Sprint type: `AUDIT_ONLY_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5BW adversarially audited the committed Sprint 5BV local-only 2018-2019 historical feature and label rebuild package. This audit reviewed the committed 5BV docs/script and the refreshed local-only export package.

This sprint did not train models, generate probabilities, generate coarse bands, create app-readable probability/band/status outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Evidence reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BV_LOCAL_ONLY_2018_2019_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `scripts/outcome_probability/build_sprint_5bv_2018_2019_historical_feature_label_rebuild.py`
- `local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/`

## 2. Provenance

After the 5BV commit, the 5BV generator was rerun from committed HEAD. The refreshed local export metadata records:

- `code_version_git_commit=ad7c6fb3b6d307601bb48fe432d0e611a2ccb1e7`
- `output_scope=internal_only_not_app_readable`
- `app_release_status=blocked_not_app_readable`
- `feature_rows=760`
- `label_rows=760`
- `blocked_rows=320`

Provenance result: pass.

## 3. Artifact Quarantine

5BV outputs remain only under:

`local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/`

The package contains local CSV/JSON/README artifacts only. The package marks outputs as `internal_only_not_app_readable`, and release blockers explicitly keep modeling, exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, and promoted artifacts blocked.

Artifact quarantine result: pass.

## 4. Import And App Isolation

Repo scan for the 5BV package path, metadata file, feature table, and label table found references only in Outcome docs and the 5BV generator script. No app, page, player-card, rankings, sorting, hidden sort key, release-service, app-loader, or promoted-artifact path references or loads 5BV outputs.

Import/app isolation result: pass.

## 5. Source Mapping And Leakage

5BV target/source mapping:

| Target season | Feature source | Label source | Audit result |
| ---: | ---: | ---: | --- |
| 2018 | completed 2017 regular season only | final 2018 regular-season stats only | pass |
| 2019 | completed 2018 regular season only | final 2019 regular-season stats only | pass |

The legality audit contains 760 emitted rows and all 760 have `legality_status=pass`. Emitted rows record `source_season_strictly_before_target=yes`, `same_season_final_stats_as_features=no`, `label_source_as_prediction_feature=no`, and `fantasy_totals_used=no`.

Leakage result: pass.

## 6. Row Counts

Generated 5BV row counts:

| Target season | QB | RB | WR | TE | Total emitted |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 51 | 98 | 147 | 81 | 377 |
| 2019 | 50 | 94 | 150 | 89 | 383 |
| Total | 101 | 192 | 297 | 170 | 760 |

Blocked rows:

| Target season | Attempted rows | Emitted rows | Blocked rows | Primary blocker |
| ---: | ---: | ---: | ---: | --- |
| 2018 | 530 | 377 | 153 | `blocked_missing_label` |
| 2019 | 550 | 383 | 167 | `blocked_missing_label` |

Blocked rows remain local-only and unscored.

## 7. NWR Scoring Reconstruction

5BV labels are rebuilt from source-safe raw components:

- passing yards, passing touchdowns, and interceptions
- rushing yards, rushing touchdowns, and rushing first downs
- receiving yards, receiving touchdowns, and receiving first downs
- rushing, receiving, and sack fumbles lost

The package does not copy fantasy totals, projections, rankings, consensus, ADP, market values, trade values/calculators, RotoWire values/outlooks/projections/rankings, legacy `private_score`, prior fantasy draft history, same-season target stats as features, or label supplement sources as prediction features.

NWR scoring reconstruction result: pass.

## 8. First-Down Completeness

First-down completeness audit:

| Row family | Season | Rows checked | Missing rushing first downs | Missing receiving first downs | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| feature_source | 2017 | 5125 | 0 | 0 | pass |
| feature_source | 2018 | 5112 | 0 | 0 | pass |
| label_source | 2018 | 5112 | 0 | 0 | pass |
| label_source | 2019 | 5079 | 0 | 0 | pass |

First-down result: pass.

## 9. Duplicate Keys And Identity

Duplicate-key audit:

| Key type | Season scope | Duplicate extra rows | Status |
| --- | --- | ---: | --- |
| source_player_week | 2017 | 0 | pass |
| source_player_week | 2018 | 0 | pass |
| feature_snapshot | 2018-2019 package | 0 | pass |
| label_row | 2018-2019 package | 0 | pass |

Identity/team/position coverage:

| Row family | Season | Rows checked | Missing player ID | Missing player name | Missing team | Missing position | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| feature_source | 2017 | 5125 | 0 | 0 | 0 | 0 | pass |
| feature_source | 2018 | 5112 | 0 | 0 | 0 | 0 | pass |
| label_source | 2018 | 5112 | 0 | 0 | 0 | 0 | pass |
| label_source | 2019 | 5079 | 0 | 0 | 0 | 0 | pass |

Duplicate-key result: pass.

Identity/team/position result: pass.

## 10. Forbidden-Field Scan

Forbidden-field scan result: pass.

No feature row uses a forbidden or quarantined field. The positive feature allowlist excludes ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, fantasy totals, EPA, WOPR/RACR/PACR/Dakota/target-share style fields, same-season target stats as preseason features, and label supplement sources as prediction features.

## 11. Population Policy

Population policy result: pass.

5BV emits historical QB/RB/WR/TE rows only. Rookies are excluded from veteran heads by requiring a completed prior-season source row. Kickers are not modeled. No rookie framework files are touched. No current 2026 rows are generated or scored.

## 12. Release And Display Stance

Release/display result: pass.

5BV and 5BW remain internal-only. Modeling is not approved. Exact percentages remain blocked. Coarse bands remain blocked. App wiring for real probabilities or bands remains blocked. Rankings/sorting and hidden sort keys remain blocked. Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but 5BV/5BW create no app-readable status table and no app-readable probability or band table.

## 13. Checks

Checks run:

- `git diff --check` passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5bv_2018_2019_historical_feature_label_rebuild.py` passed
- `ruff check scripts/outcome_probability/build_sprint_5bv_2018_2019_historical_feature_label_rebuild.py` unavailable locally; no package installation performed
- `python -m pytest tests/test_nwr_outcome_constrained_ordinal_prototype_service.py -q` unavailable locally; no package installation performed

## 14. Final Verdict

5BW audit verdict: `GREEN`.

The 5BV package is approved for internal audit commit only. It is not approved for modeling, exact percentages, coarse bands, app display, rankings/sorting, hidden sort keys, or promoted artifacts.
