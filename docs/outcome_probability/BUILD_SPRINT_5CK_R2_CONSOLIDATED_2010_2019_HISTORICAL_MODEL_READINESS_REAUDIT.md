# Sprint 5CK-R2: Consolidated 2010-2019 Historical Model-Readiness Re-Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_INTERNAL_ONLY_MODEL_READINESS_REAUDIT`

Sprint type: `CONSOLIDATED_READINESS_AUDIT_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CK-R2 reran the consolidated 2010-2019 historical package readiness audit after Sprint 5CK-R committed the accepted-blocker contract for the single Taysom Hill 2018 QB to 2019 TE source/target mismatch exclusion.

This sprint did not train models, score players, create probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie files, edit `data/`, edit raw source data, or create promoted artifacts.

## 2. Audited Packages

| Package | Target seasons | Source dependency | Feature rows | Label rows | Blocked rows |
| --- | --- | --- | ---: | ---: | ---: |
| 5CI | 2010-2011 | 2010 uses 2009; 2011 uses 2010 | 749 | 749 | 248 |
| 5CF | 2012-2013 | 2012 uses 2011; 2013 uses 2012 | 754 | 754 | 279 |
| 5CC | 2014-2015 | 2014 uses 2013; 2015 uses 2014 | 760 | 760 | 276 |
| 5BZ | 2016-2017 | 2016 uses 2015; 2017 uses 2016 | 778 | 778 | 300 |
| 5BV | 2018-2019 | 2018 uses 2017; 2019 uses 2018 | 760 | 760 | 320 |
| Total | 2010-2019 | completed prior-season sources only | 3801 | 3801 | 1423 |

Package coverage result: pass. Local historical package coverage exists for all target seasons 2010 through 2019.

## 3. Local-Only Re-Audit Export

Created local-only audit export:

`local_exports/outcome_probability/sprint_5ck_r2_consolidated_2010_2019_historical_model_readiness_reaudit/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5ck.json` | audit verdict, counts, blocker contract, release-blocker flags | no |
| `package_inventory.csv` | package-level row counts and lineage metadata | no |
| `rows_by_target_season_position.csv` | usable row counts by target season and position | no |
| `blocked_rows_by_target_season_position_reason.csv` | blocked-row counts by season, position, and reason | no |
| `accepted_excluded_blocker_contract.csv` | the exact accepted 5CK-R excluded blocker | no |
| `unaccepted_non_missing_label_blockers.csv` | non-accepted blocker audit, empty when GREEN | no |
| `label_support_by_head_season_position.csv` | support counts by season, position, and head | no |
| `support_readiness_by_head.csv` | support-only readiness labels by head | no |
| `consolidated_duplicate_key_audit.csv` | duplicate-key audit rollup | no |
| `consolidated_identity_team_position_audit.csv` | identity/team/position audit rollup | no |
| `consolidated_first_down_completeness.csv` | first-down completeness rollup | no |
| `consolidated_forbidden_feature_scan.csv` | forbidden-field quarantine rollup | no |
| `README_SPRINT_5CK.md` | local audit summary | no |

All 5CK-R2 exports are internal-only and not app-readable.

## 4. Usable Rows By Season And Position

| Target season | QB | RB | WR | TE | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 62 | 94 | 132 | 80 | 368 |
| 2011 | 58 | 91 | 153 | 79 | 381 |
| 2012 | 51 | 97 | 144 | 83 | 375 |
| 2013 | 53 | 102 | 143 | 81 | 379 |
| 2014 | 58 | 97 | 137 | 81 | 373 |
| 2015 | 60 | 102 | 138 | 87 | 387 |
| 2016 | 53 | 110 | 141 | 81 | 385 |
| 2017 | 57 | 104 | 147 | 85 | 393 |
| 2018 | 51 | 98 | 147 | 81 | 377 |
| 2019 | 50 | 94 | 150 | 89 | 383 |
| Total | 553 | 989 | 1432 | 827 | 3801 |

## 5. Blocked Rows

Blocked-row result: pass under the committed 5CK-R accepted-blocker contract.

| Block reason | Rows | Readiness treatment |
| --- | ---: | --- |
| `blocked_missing_label` | 1422 | expected missing target-season label blocker |
| `blocked_source_target_position_mismatch` | 1 | accepted excluded 5CK-R blocker only |

No unaccepted non-missing-label blockers remain.

## 6. Accepted Excluded Blocker

Accepted excluded blocker result: pass.

| Package | Player ID | Player | Source season | Target season | Source position | Target position | Reason |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| 5BV | `00-0033357` | Taysom Hill | 2018 | 2019 | QB | TE | `blocked_source_target_position_mismatch` |

The accepted blocker count is exactly one. The row remains excluded from usable feature/label rows and is not app-readable.

## 7. Quality Gates

| Gate | Result |
| --- | --- |
| Duplicate keys | pass |
| Identity/team/position | pass |
| First-down completeness | pass |
| Forbidden-field quarantine | pass |
| Output quarantine | pass |
| App/import isolation | pass |
| Return-stat limitation documented | pass |

The return-stat limitation remains active: granular `return_yards` and `return_tds` are unavailable from `player_stats.csv` alone, so return scoring is not included.

## 8. Support-Only Readiness

The consolidated support-only head inventory produced:

| Support label | Heads |
| --- | ---: |
| `GREEN_SUPPORT_ONLY_FUTURE_EXPERIMENT_ELIGIBLE` | 14 |
| `YELLOW_SUPPORT_CONSTRAINED` | 5 |

These are internal support-readiness labels only. They are not player-facing probabilities, exact percentages, coarse bands, app labels, rankings, or hidden sort keys.

## 9. Recommendation

5CK-R2 recommendation: `GREEN`.

The consolidated 2010-2019 local historical package foundation is clean enough to proceed to Sprint 5CL support-count evaluation.

This does not approve model training. It only approves the next packet gate: local-only threshold-head support evaluation using counts.

## 10. Release Stance

Model training remains blocked.

Probabilities remain blocked.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

No app-readable probability, band, or status output was created.

## 11. Checks

Checks run:

- `python scripts\outcome_probability\audit_sprint_5ck_consolidated_historical_model_readiness.py` passed
- `python -m py_compile scripts\outcome_probability\audit_sprint_5ck_consolidated_historical_model_readiness.py` passed
- `git diff --check` passed

Ruff was not run because it is optional and no package installation is allowed. Pytest was not required because no production code or tests changed.
