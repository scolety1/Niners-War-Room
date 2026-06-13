# Sprint 5BJ 5BI Holdout Calibration Audit

## 1. Executive verdict

Audit verdict: `GREEN`

5BI commit audited: `496bc29 Build 5BI internal holdout calibration package`

Sprint 5BJ audited the committed 5BI report and builder script plus the existing local-only 5BI export package. The audit found no app-readable output, no app wiring, no ranking/sorting contamination, no rookie framework edits, no promoted artifact, and no release overclaim.

Resolved provenance note: the first 5BJ audit found local-export metadata with pre-commit `code_version_git_commit=126c6ce`, because the local-only exports were generated before the 5BI commit `496bc29`. The committed 5BI generator was rerun from current HEAD, and `metadata_sprint_5bi.json` now records `code_version_git_commit=496bc29d05f2b63621254eaae686a647ffe4569a`.

Release stance remains blocked:

- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.

## 2. Files/artifacts audited

Committed 5BI files:

- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `scripts/outcome_probability/build_sprint_5bi_internal_holdout_calibration_package.py`

Related constrained prototype files:

- `src/services/nwr_outcome_constrained_ordinal_prototype_service.py`
- `tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`

Local-only 5BI exports reviewed, not staged and not committed:

- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/`

## 3. Commit and file-scope audit

Commit `496bc29` changed only:

- the 5BI report under `docs/outcome_probability/`
- the 5BI builder under `scripts/outcome_probability/`

No rookie framework files were touched. No app files were touched. No ranking, sorting, value, player-card, release-service, or app-loader files were touched.

## 4. Artifact quarantine result

Result: pass.

The 5BI script writes to:

`local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/`

Generated quarantine evidence:

| Gate | Status | Evidence |
|---|---|---|
| Output folder scope | pass | active outcome worktree `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package` |
| App-readable probability table | pass | no app path is written; every row marks `app_readable=no` |
| Ranking/sorting output | pass | every prediction row sets `sort_allowed=no` and `ranking_use_allowed=no` |
| Promoted model artifact | pass | no pickle, joblib, model package, app table, or promoted artifact is written |

Resolved provenance check:

- The first audit found local metadata at `code_version_git_commit=126c6ce`.
- The 5BI generator was rerun from the audited committed 5BI code.
- Refreshed local metadata now records `code_version_git_commit=496bc29d05f2b63621254eaae686a647ffe4569a`.

## 5. Import/app isolation result

Result: pass.

Scans for 5BI export names and builder names found references only in:

- `scripts/outcome_probability/build_sprint_5bi_internal_holdout_calibration_package.py`
- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- prior 5BH/5BI docs references

No 5BI references were found in `app/` or app-loading paths. No Streamlit display wiring, player card wiring, rankings table wiring, sorting key, hidden sort key, release service, or app loader consumes 5BI outputs.

## 6. Forbidden feature scan result

Result: pass.

The local 5BI forbidden-feature scan reports 13 pass rows and 0 blockers.

5BI feature list uses canonical prior-season features only:

- age and experience
- prior-season NWR PPG / finish-rank
- prior completed-season games, first downs, receptions, rushing/receiving/passing yards

Forbidden source/features were absent:

- ADP
- public rankings
- projections
- consensus
- market values
- trade values or calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- same-season final stats as preseason features
- label supplement sources as prediction features

## 7. Split discipline result

Result: pass.

Generated split audit:

| Gate | Status | Evidence |
|---|---|---|
| Train/validation/test split | pass | train=834; validation=260; test=261 |
| Same-season final stats as features | pass | 5X/5N feature snapshots use completed prior-season feature lineage |

The script uses:

- Train: 2020-2022
- Validation: 2023
- Test: 2024

Same-season labels are used only as holdout outcomes, not preseason features.

## 8. Population policy result

Result: pass.

Generated population audit:

| Gate | Status | Evidence |
|---|---|---|
| Waived/unscored players | pass | historical holdout rows only; no current waived player scoring |
| Rookies | pass | `rookie_rows_scored=0` |
| Kickers | pass | `kicker_rows_scored=0` |
| Blocked current rows | pass | no blocked 2026 rows are scored |

The script limits modeled positions to RB/WR and the holdout seasons to 2023/2024 validation/test rows after training on 2020-2022.

## 9. Holdout-row audit

Result: pass.

The 5BI prediction export contains validation/test rows only:

| Split | Target season | Method | Rows |
|---|---:|---|---:|
| Validation | 2023 | Raw independent baseline | 1,300 |
| Validation | 2023 | Post-hoc forward clamp benchmark | 1,300 |
| Validation | 2023 | Constrained/PAVA candidate | 1,300 |
| Test | 2024 | Raw independent baseline | 1,305 |
| Test | 2024 | Post-hoc forward clamp benchmark | 1,305 |
| Test | 2024 | Constrained/PAVA candidate | 1,305 |

There are no 2026 release rows in the 5BI prediction export.

All 7,815 prediction rows have:

- `app_readable=no`
- `sort_allowed=no`
- `ranking_use_allowed=no`
- `exact_percentage_display_allowed=no`
- `coarse_band_display_allowed=no`

## 10. Monotonicity result

Result: pass for clamped and constrained methods; raw remains blocked.

The threshold semantics match the 5BB top-N-or-better contract:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

| Split | Position | Method | Players checked | Adjacent violations | Max adjacent gap |
|---|---|---|---:|---:|---:|
| Validation | RB | Raw independent baseline | 106 | 18 | 0.072433 |
| Validation | WR | Raw independent baseline | 154 | 80 | 0.009098 |
| Test | RB | Raw independent baseline | 98 | 17 | 0.050787 |
| Test | WR | Raw independent baseline | 163 | 79 | 0.011474 |
| Validation/Test | RB/WR | Post-hoc forward clamp benchmark | all checked | 0 | 0.000000 |
| Validation/Test | RB/WR | Constrained/PAVA candidate | all checked | 0 | 0.000000 |

Monotonicity success does not authorize release because calibration stability fails.

## 11. Metric/calibration honesty result

Result: pass.

5BI compares raw, clamped, and constrained methods consistently on the same validation/test holdout rows. Brier and log-loss are computed from holdout predictions and binary top-N labels. No calibration layer is fit or promoted.

Average metric summary across 10 RB/WR heads:

| Split | Method | Average Brier | Average log loss |
|---|---|---:|---:|
| Validation | Raw independent baseline | 0.096871 | 0.310235 |
| Validation | Post-hoc forward clamp benchmark | 0.097012 | 0.310614 |
| Validation | Constrained/PAVA candidate | 0.096857 | 0.310188 |
| Test | Raw independent baseline | 0.095936 | 0.307181 |
| Test | Post-hoc forward clamp benchmark | 0.095949 | 0.307363 |
| Test | Constrained/PAVA candidate | 0.095883 | 0.307038 |

Calibration finding is honest and release-blocking:

| Split | Method | Unstable heads | Total heads | Max absolute calibration gap | Minimum bin events |
|---|---|---:|---:|---:|---:|
| Validation | Raw independent baseline | 10 | 10 | 0.350186 | 0 |
| Validation | Post-hoc forward clamp benchmark | 10 | 10 | 0.350186 | 0 |
| Validation | Constrained/PAVA candidate | 10 | 10 | 0.350186 | 0 |
| Test | Raw independent baseline | 10 | 10 | 0.272990 | 0 |
| Test | Post-hoc forward clamp benchmark | 10 | 10 | 0.272990 | 0 |
| Test | Constrained/PAVA candidate | 10 | 10 | 0.272990 | 0 |

All 10 RB/WR heads remain unstable on validation and test for every method.

## 12. Release recommendation

Final recommendation: internal-only, blocked for release.

5BI can continue as internal research evidence. It does not permit app display, probability release, coarse-band release, ranking/sorting use, or promoted artifacts.

## 13. Provenance closure

The 5BI local-only exports were regenerated from current HEAD after the 5BI commit. The refreshed metadata now records the audited commit hash:

`496bc29d05f2b63621254eaae686a647ffe4569a`

The regenerated exports remain uncommitted. Next safe sprint remains an HQ decision. No release/display work should proceed without explicit approval.

## 14. Final gate label

Final gate label: `GREEN_INTERNAL_ONLY_AUDIT_PASS_PROVENANCE_RESOLVED`

Meaning:

- Artifact quarantine passes.
- Import/app isolation passes.
- Forbidden feature scan passes.
- Split discipline passes.
- Population policy passes.
- Constrained/PAVA monotonicity passes.
- Metric/calibration claims are honest.
- The initial local export provenance warning was resolved by rerunning the 5BI generator from commit `496bc29`.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
