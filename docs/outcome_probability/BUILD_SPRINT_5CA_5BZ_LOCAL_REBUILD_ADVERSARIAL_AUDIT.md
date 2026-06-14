# Sprint 5CA: 5BZ Local Rebuild Adversarial Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_FOR_INTERNAL_AUDIT_COMMIT_RELEASE_DISPLAY_BLOCKED`

Audited 5BZ commit: `c07ea94`

Sprint type: `AUDIT_ONLY_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CA adversarially audited the committed Sprint 5BZ local-only 2016-2017 historical feature and label rebuild package. This audit reviewed the committed 5BZ docs/script and the refreshed local-only export package.

This sprint did not train models, generate probabilities, generate coarse bands, create app-readable probability/band/status outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Evidence reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BZ_LOCAL_ONLY_2016_2017_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `scripts/outcome_probability/build_sprint_5bz_2016_2017_historical_feature_label_rebuild.py`
- `local_exports/outcome_probability/sprint_5bz_2016_2017_historical_feature_label_rebuild/`

## 2. Provenance

After the 5BZ commit, the 5BZ generator was rerun from committed HEAD. The refreshed local export metadata records:

- `code_version_git_commit=c07ea9470955303ec9d3f80374e29c98ea89db83`
- `output_scope=internal_only_not_app_readable`
- `app_release_status=blocked_not_app_readable`
- `feature_rows=778`
- `label_rows=778`
- `blocked_rows=300`

Provenance result: pass.

## 3. Artifact Quarantine

5BZ outputs remain only under:

`local_exports/outcome_probability/sprint_5bz_2016_2017_historical_feature_label_rebuild/`

The package contains local CSV/JSON/README artifacts only. Outputs are marked `internal_only_not_app_readable`, and release blockers explicitly keep modeling, exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, and promoted artifacts blocked.

Artifact quarantine result: pass.

## 4. Import And App Isolation

Repo scan for the 5BZ package path, metadata file, feature table, and label table found references only in Outcome docs and the 5BZ generator script. No app, page, player-card, rankings, sorting, hidden sort key, release-service, app-loader, or promoted-artifact path references or loads 5BZ outputs.

Import/app isolation result: pass.

## 5. Feature And Label Legality

5BZ target/source mapping:

| Target season | Feature source | Label source | Audit result |
| ---: | ---: | ---: | --- |
| 2016 | completed 2015 regular season only | final 2016 regular-season stats only | pass |
| 2017 | completed 2016 regular season only | final 2017 regular-season stats only | pass |

The legality audit contains 778 emitted rows and all 778 have `legality_status=pass`. Same-season final stats are labels only and are not used as preseason features.

Leakage result: pass.

## 6. Row Counts And Blocked Rows

Generated 5BZ row counts:

| Target season | QB | RB | WR | TE | Total emitted |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 53 | 110 | 141 | 81 | 385 |
| 2017 | 57 | 104 | 147 | 85 | 393 |
| Total | 110 | 214 | 288 | 166 | 778 |

Blocked rows:

| Target season | Attempted rows | Emitted rows | Blocked rows | Primary blocker |
| ---: | ---: | ---: | ---: | --- |
| 2016 | 536 | 385 | 151 | `blocked_missing_label` |
| 2017 | 542 | 393 | 149 | `blocked_missing_label` |

Blocked rows are preserved in local-only artifacts and are not silently modeled.

## 7. NWR Scoring Reconstruction

5BZ labels are rebuilt from source-safe raw components:

- passing yards, passing touchdowns, and interceptions
- rushing yards, rushing touchdowns, and rushing first downs
- receiving yards, receiving touchdowns, and receiving first downs
- rushing, receiving, and sack fumbles lost

The package does not copy fantasy totals, projections, rankings, consensus, ADP, market values, trade values/calculators, RotoWire values/outlooks/projections/rankings, legacy `private_score`, prior fantasy draft history, same-season target stats as features, or label supplement sources as prediction features.

NWR scoring reconstruction result: pass.

## 8. First Downs, Duplicate Keys, And Identity

First-down completeness:

| Row family | Season | Rows checked | Missing rushing first downs | Missing receiving first downs | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| feature_source | 2015 | 5109 | 0 | 0 | pass |
| feature_source | 2016 | 5086 | 0 | 0 | pass |
| label_source | 2016 | 5086 | 0 | 0 | pass |
| label_source | 2017 | 5125 | 0 | 0 | pass |

Duplicate-key audit:

| Key type | Season scope | Duplicate extra rows | Status |
| --- | --- | ---: | --- |
| source_player_week | 2015 | 0 | pass |
| source_player_week | 2016 | 0 | pass |
| feature_snapshot | 2016-2017 package | 0 | pass |
| label_row | 2016-2017 package | 0 | pass |

Identity/team/position coverage has complete `player_id`, `player_display_name`, team, position, and position group coverage. Some historical 2015 and 2016 rows have blank `player_name`, but `player_display_name` is complete and used as a safe local fallback. No emitted row is blocked by identity/team/position gaps.

First-down result: pass.

Duplicate-key result: pass.

Identity/team/position result: pass with documented display-name fallback.

## 9. Forbidden-Field Scan

Forbidden-field scan result: pass.

No feature row uses a forbidden or quarantined field. The positive feature allowlist excludes ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, fantasy totals, EPA, WOPR/RACR/PACR/Dakota/target-share style fields, same-season target stats as preseason features, and label supplement sources as prediction features.

## 10. Population Policy

Population policy result: pass.

5BZ emits historical QB/RB/WR/TE rows only. Rookies are excluded from veteran heads by requiring a completed prior-season source row. Kickers are not modeled. No rookie framework files are touched. No current 2026 rows are generated or scored.

## 11. Release And Display Stance

Release/display result: pass.

5BZ and 5CA remain internal-only. Modeling is not approved. Exact percentages remain blocked. Coarse bands remain blocked. App wiring for real probabilities or bands remains blocked. Rankings/sorting and hidden sort keys remain blocked. Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but 5BZ/5CA create no app-readable status table and no app-readable probability or band table.

## 12. Checks

Checks run:

- `git diff --check` passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5bz_2016_2017_historical_feature_label_rebuild.py` passed
- `ruff check scripts/outcome_probability/build_sprint_5bz_2016_2017_historical_feature_label_rebuild.py` unavailable locally; no package installation performed
- `python -m pytest tests/test_nwr_outcome_constrained_ordinal_prototype_service.py -q` unavailable locally; no package installation performed

## 13. Final Verdict

5CA audit verdict: `GREEN`.

The 5BZ package is approved for internal audit commit only. It is not approved for modeling, exact percentages, coarse bands, app display, rankings/sorting, hidden sort keys, or promoted artifacts.
