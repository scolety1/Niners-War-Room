# Sprint 5AZ Threshold Evaluation Adversarial Audit

## Status

Verdict: `THRESHOLD_EVALUATION_AUDIT_PASS_WITH_WARNINGS`

Canonical gate label: `PASS_INTERNAL_ONLY_CONTINUE_RESEARCH`

This gate label means exact percentages remain blocked, app wiring remains blocked, coarse-band candidates remain internal research-only, and no head is app-ready.

Sprint 5AZ adversarially audited the Sprint 5AY partial threshold model evaluation before any app, display, or release discussion. The audit found no evidence that Sprint 5AY created app-readable probabilities, app wiring, rankings/sorting outputs, fake predictions for unscored players, rookie probabilities through veteran heads, decision automation, or promoted model artifacts.

The warning is substantive: Sprint 5AY produced internal player-level probability values in a local-only export. Those values are correctly marked as not app-readable, not sortable, not player-facing, and not display-ready, but they must remain quarantined. Exact percentages remain blocked. App wiring remains blocked.

## Scope

Audited Sprint 5AY local outputs under:

`local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/`

Created Sprint 5AZ local-only exports under:

`local_exports/outcome_probability/sprint_5az_threshold_evaluation_adversarial_audit/`

Created outputs:

- `threshold_output_risk_audit.csv`
- `threshold_leakage_audit.csv`
- `threshold_calibration_claims_audit.csv`
- `threshold_monotonicity_audit.csv`
- `threshold_coverage_risk_audit.csv`
- `threshold_release_recommendation_audit.csv`
- `audit_findings.csv`
- `metadata_sprint_5az.json`
- `README_SPRINT_5AZ.md`

## Output-Risk Audit

| Risk area | Result | Evidence |
|---|---|---|
| App-readable probability tables | pass | Sprint 5AY coverage reports `app_probability_files_created=0`; prediction output exists only under `local_exports`. |
| Player-facing probabilities | pass | Rows allowing exact display: 0. Rows allowing coarse display: 0. |
| Rankings/sorting outputs | pass | `sort_allowed` rows: 0. `ranking_use_allowed` rows: 0. App/source references to Sprint 5AY export names: 0. |
| Hidden sortable values | pass with warning | The internal player-level CSV has `internal_probability_unreleased`, but every row has `sort_allowed=no` and `ranking_use_allowed=no`. |
| Decision automation | pass | No decision automation output was found or wired. |
| Promoted model artifacts | pass | Sprint 5AY metadata has `model_artifact_saved=false`; coverage reports 0 promoted artifacts. |
| App wiring | pass | App/source references to 5AY export names: 0. App/source references to 5AY display/sort flags: 0. |
| Fake probabilities for unscored players | pass | The five waived priority players are absent from the prediction export; non-ready source rows: 0. |
| Rookie probabilities through veteran heads | pass | Prediction rows are only QB/RB/WR/TE veteran-head rows; rookies remain excluded. |

Prediction export row counts reviewed:

- QB: 296
- RB: 625
- WR: 1,005
- TE: 600
- Total player-head rows: 2,526

These rows remain internal-only. They must not be copied into app data, default tables, hidden columns, ranking logic, sorting logic, or decision automation.

## Leakage And Schema Audit

Result: pass.

The Sprint 5AY forbidden-feature scan passed for all 14 evaluated legal feature names. No forbidden feature fragments were found in the evaluated feature set.

Confirmed absent from prediction features:

- ADP
- public rankings
- projections
- market or trade values
- prior fantasy draft history
- RotoWire ranking, projection, outlook, or value fields
- legacy `private_score`
- same-season final stats as features
- label supplement sources as prediction features
- old ambiguous feature names

Note: `prior_season_nwr_finish_rank` is a factual prior completed-season finish-rank feature from the renamed prior-season feature schema. It is not a current app ranking, market value, or display ranking.

## Calibration-Claims Audit

Result: pass with release-blocking warnings.

Sprint 5AY did not overstate calibration readiness:

- Exact percentages remain blocked.
- All heads had unstable calibration bins.
- No Platt calibration layer was promoted.
- No isotonic calibration layer was promoted.
- No calibrated probability artifact was saved.
- Sparse heads were marked `blocked_sparse_events`.
- Coarse-band candidates were marked `coarse_band_research_only`, not app-ready.

Sparse heads correctly blocked:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

Unstable-calibration heads correctly blocked:

- `same_year_qb_t12`
- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_te_t12`
- `same_year_te_t18`
- `same_year_te_t24`

## Monotonicity Audit

Result: pass with exact-percentage blockers.

| Position | Rows checked | Violating rows | Violation rate | Max adjacent gap | Audit result |
|---|---:|---:|---:|---:|---|
| QB | 74 | 0 | 0.000000 | 0.000000 | pass |
| RB | 125 | 3 | 0.024000 | 0.012789 | warning, blocks exact percentages |
| WR | 201 | 15 | 0.074627 | 0.002894 | warning, blocks exact percentages |
| TE | 120 | 0 | 0.000000 | 0.000000 | pass |

RB violations:

- `same_year_rb_t36>same_year_rb_t48`: 3

WR violations:

- `same_year_wr_t12>same_year_wr_t24`: 15
- `same_year_wr_t6>same_year_wr_t12`: 12

These failures are enough to block exact percentages and player-facing display. A future sprint would need monotonic post-processing, jointly constrained heads, or another threshold-chain repair strategy before release. Coarse-band research may continue only as internal research with these warnings attached.

## Coverage-Risk Audit

Result: pass with release-blocking warnings.

| Coverage item | Count | Status | Release impact |
|---|---:|---|---|
| Ready 2026 veteran feature rows | 520 | scored internal-only | Supports internal research only; does not authorize display. |
| Blocked 2026 veteran feature rows | 172 | not scored | Blocks exact percentages and future app display until resolved or explicitly waived. |
| Top-priority waived players missing features | 5 | not scored | Blocks complete app-facing release; waiver allowed partial research only. |
| Rookie rows | 80 | excluded separate path | Not in veteran threshold scope. |
| Kicker rows | 8 | not applicable | Not applicable. |
| Player-level output rows | 2,526 | internal-only not released | Must remain local-only and not app-readable. |
| App probability files created | 0 | none | No app probability file created. |
| Promoted model artifacts created | 0 | none | No promoted artifact created. |

The five waived priority players remain unscored:

- Brandon Aiyuk
- Joe Mixon
- Tank Dell
- Jonathon Brooks
- MarShawn Lloyd

This partial coverage blocks exact percentages and app display. It does not block quarantined internal coarse-band research as long as the coverage warning remains attached and no missing players are imputed or faked.

## Release-Recommendation Audit

Result: pass with warnings.

All 19 heads use allowed, non-app-ready classifications:

| Classification | Count | Heads |
|---|---:|---|
| `blocked_sparse_events` | 5 | `same_year_qb_t6`, `same_year_rb_t6`, `same_year_wr_t6`, `same_year_te_t3`, `same_year_te_t6` |
| `blocked_unstable_calibration` | 6 | `same_year_qb_t12`, `same_year_qb_t18`, `same_year_qb_t24`, `same_year_te_t12`, `same_year_te_t18`, `same_year_te_t24` |
| `coarse_band_research_only` | 8 | `same_year_rb_t12`, `same_year_rb_t24`, `same_year_rb_t36`, `same_year_rb_t48`, `same_year_wr_t12`, `same_year_wr_t24`, `same_year_wr_t36`, `same_year_wr_t48` |

No head is app-ready. No head is approved for rankings-table display. No head is approved for sorting. No head is approved for exact percentage display.

## Final Recommendation

Recommendation: `CONTINUE_INTERNAL_COARSE_BAND_RESEARCH_ONLY`

Sprint 5AY did not overclaim release readiness, and Sprint 5AZ did not find output leakage or app-wiring risk in the current repo state. Coarse-band research may continue for the eight RB/WR research candidates, but only as local, internal, quarantined research.

Exact percentages remain blocked. App wiring remains blocked. Rankings-table display remains blocked. Sorting remains blocked. Player-detail display remains blocked. Promoted model artifacts remain blocked.

## Explicit Non-Actions

- No new models were trained.
- No app probabilities were created.
- No fake or placeholder probabilities were created.
- No app-readable probability tables were created.
- No probabilities were wired into app pages.
- No rankings or sorting changes were made.
- No decision automation was created.
- No model artifact was promoted.
- No push or deploy occurred.
