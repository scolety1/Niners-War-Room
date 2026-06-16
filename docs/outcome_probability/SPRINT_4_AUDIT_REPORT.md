# Sprint 4 Audit Report

Verdict: `PASS`

Sprint 4 is a limited internal v0 historical base-rate scaffold only. It does not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, or deploy.

## Files Audited

- `src/services/nwr_outcome_base_rate_service.py`
- `tests/test_nwr_outcome_base_rate_service.py`
- `docs/outcome_probability/BUILD_SPRINT_4_V0_BASE_RATES.md`

Sprint 1/2/3/3B regression tests were also run.

## Scope And Source

- Canonical source: `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`
- Scope: `limited_truth_set_v0`
- Component waiver: `truth_set_v0_component_waiver_v1`
- Export folder: `local_exports/outcome_probability/sprint_4_v0_base_rates/`

Exports remain local/internal only.

## Audit Findings

1. Sprint 4 avoided calibrated models, app percentages, rankings, push, and deploy.
2. Output rows are marked with `scope = limited_truth_set_v0`.
3. Output rows carry `component_waiver_id = truth_set_v0_component_waiver_v1`.
4. Imported fantasy totals are rejected as label sources.
5. Forbidden fields are blocked before base-rate construction.
6. `rookie_post_draft` is excluded.
7. Included row families are limited to:
   - `all_player_pre_week1`
   - `offseason_carryover`
8. Supported outcomes are limited to:
   - `same_year_difference_maker`
   - `same_year_starter`
   - `same_year_useful`
   - `same_year_replacement_or_bust`
   - `next_year_starter`
9. Censored/null labels are excluded from denominators.
10. Raw rates are retained for audit, while `posterior_mean` is emitted as the smoothed value.
11. Beta-binomial smoothing is implemented as:
    `posterior_mean = (success_raw + prior_alpha) / (n_raw + prior_alpha + prior_beta)`.
12. Sparse buckets fall back toward parent priors through beta prior alpha/beta values.
13. Reliability flags are assigned using the Sprint 4 thresholds.
14. Exports are written only under `local_exports/outcome_probability/sprint_4_v0_base_rates/`.
15. Documentation clearly states the outputs are not calibrated probabilities and are not app-ready.

## Repair Made During Audit

The audit found that `base_rate_reliability_report.csv` and `base_rate_leakage_guardrail_report.csv` had `scope` but were missing `component_waiver_id`. This was a Sprint 4 contract issue because every output must carry the waiver.

Repair:

- Added `component_waiver_id` to reliability report rows.
- Added `component_waiver_id` to leakage guardrail report rows.
- Strengthened `tests/test_nwr_outcome_base_rate_service.py` to assert every output group carries both `scope` and `component_waiver_id`.
- Regenerated local Sprint 4 exports.

## Export Readbacks

- `base_rate_bucket_results.csv`: 530 rows, all `limited_truth_set_v0` / `truth_set_v0_component_waiver_v1`.
- `base_rate_parent_priors.csv`: 80 rows.
- `base_rate_censoring_report.csv`: `next_year_starter` has 96 observed rows and 70 censored/null rows excluded.
- `base_rate_reliability_report.csv`: `C=30`, `D=484`, `UNPUBLISHABLE=16`.
- `base_rate_leakage_guardrail_report.csv`: forbidden field scan passed, imported fantasy total rejection passed, rookie post-draft exclusion passed.

## Tests Run

Command:

```powershell
python -m pytest tests/test_nwr_outcome_base_rate_service.py tests/test_nwr_outcome_source_manifest_service.py tests/test_nwr_outcome_historical_row_factory.py tests/test_nwr_outcome_training_row_service.py tests/test_nwr_outcome_scoring_service.py tests/test_outcome_probability_build_packet.py -q
```

Result: `61 passed`.

Additional checks:

```powershell
python -m py_compile src/services/nwr_outcome_base_rate_service.py tests/test_nwr_outcome_base_rate_service.py
ruff check src/services/nwr_outcome_base_rate_service.py tests/test_nwr_outcome_base_rate_service.py
git diff --check
```

Results:

- `py_compile`: passed.
- `ruff`: passed.
- `git diff --check`: passed with pre-existing LF/CRLF warnings on unrelated outcome-column prep files.

## Smoothing, Reliability, And Censoring Issues

No remaining blocker found.

Notes:

- Reliability remains intentionally conservative because this is a small truth-set universe.
- `UNPUBLISHABLE` buckets remain internal and should not be surfaced.
- These base rates are not calibrated probabilities.

## Leakage Concerns

No leakage blocker found in Sprint 4 outputs.

Guardrails still in force:

- Imported fantasy totals rejected.
- ADP, FantasyPros, public rankings, consensus, startup rankings, trade calculators, public projections, RotoWire projections/rankings/outlooks/values, market rank, league rank, prior fantasy draft history, and legacy `private_score` remain forbidden.

## Commit Readiness

Sprint 4 files are safe to commit separately.

Exact Sprint 4-only add list:

```powershell
git add -- `
  src/services/nwr_outcome_base_rate_service.py `
  tests/test_nwr_outcome_base_rate_service.py `
  docs/outcome_probability/BUILD_SPRINT_4_V0_BASE_RATES.md `
  docs/outcome_probability/SPRINT_4_AUDIT_REPORT.md
```

Do not force-add ignored `local_exports` unless explicitly requested.

## Next Step

Sprint 4B should run before Sprint 5.

Recommended Sprint 4B scope:

- audit bucket quality and sparse bucket behavior,
- review component waiver sensitivity,
- decide whether rare components should remain waived or be supplemented,
- verify whether truth-set base rates are useful enough before any calibrated modeling.

Calibrated model work remains blocked for production/app use.
