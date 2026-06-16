# Sprint 4C Audit Report

Verdict: PASS

Sprint 4C creates a collapsed internal v0 benchmark layer from Sprint 4 base-rate rows. It does not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, or deploy.

## Files Audited

- `src/services/nwr_outcome_base_rate_service.py`
- `tests/test_nwr_outcome_base_rate_service.py`
- `docs/outcome_probability/BUILD_SPRINT_4C_COLLAPSED_V0_BENCHMARK.md`

## Audit Findings

| Question | Result | Notes |
| --- | --- | --- |
| Outputs internal/local only | PASS | Exports write to `local_exports/outcome_probability/sprint_4c_collapsed_v0_benchmark/`; no app integration exists. |
| Direct bucket families limited to `position`, `position_cohort` | PASS | `COLLAPSED_DIRECT_BENCHMARK_FAMILIES` contains only those two families. |
| Tier bucket families collapsed to parent lineage | PASS | `prior_finish_tier`, `trailing_ppg_tier`, and `games_played_tier` emit lineage action `collapsed_to_parent`, not direct benchmark rows. |
| `age_band` disabled | PASS | `age_band` emits `disabled_missing_age` in disabled family and lineage outputs. |
| Same-year outcomes only | PASS | Kept outcomes are same-year difference-maker, starter, useful, and replacement-or-bust. |
| `next_year_starter` disabled | PASS | `next_year_starter` emits `disabled_censored_or_unstable`. |
| Benchmark rows carry waiver, scope, and internal flag | PASS | Rows carry `component_waiver_id=truth_set_v0_component_waiver_v1`, `scope=limited_truth_set_v0`, and `internal_only=true`. |
| Disabled reasons documented | PASS | Disabled family/outcome rows include explicit disabled reasons; build doc explains the policy. |
| Local export path isolated | PASS | Export helper writes only to caller-provided Sprint 4C folder; generated outputs are under the required local export path. |
| No calibrated probabilities/app percentages/rankings/push/deploy | PASS | No app, ranking, deployment, or calibrated model files were changed. |

## Export Readback

Current local Sprint 4C export summary:

- Collapsed benchmark rows: `64`
- `usable_internal_parent_prior`: `16`
- `sparse_internal_prior`: `48`
- Published direct internal benchmark lineage rows: `64`
- Collapsed-to-parent lineage rows: `328`
- Disabled outcome lineage rows: `106`
- Disabled bucket-family lineage rows: `32`

## Small Audit Cleanup

The initial Sprint 4C implementation used `internal_only=yes`. The audit contract asked for `internal_only=true`, so the service, test expectation, local Sprint 4C exports, and build doc were normalized to `true`.

## Leakage And App-Probability Review

No leakage or app-probability concern found. Sprint 4C only consumes already-built Sprint 4 base-rate bucket rows and does not add predictive inputs, player probabilities, app percentage values, or rankings.

## Commit Safety

Sprint 4C files are safe to commit separately after checks pass:

```powershell
git add -- `
  src/services/nwr_outcome_base_rate_service.py `
  tests/test_nwr_outcome_base_rate_service.py `
  docs/outcome_probability/BUILD_SPRINT_4C_COLLAPSED_V0_BENCHMARK.md `
  docs/outcome_probability/SPRINT_4C_AUDIT_REPORT.md
```

Do not add ignored `local_exports` unless explicitly requested.

## Sprint 4D / Sprint 5 Recommendation

Sprint 4D should run before Sprint 5. Sprint 5 calibrated modeling remains blocked until the collapsed benchmark is reviewed and the remaining source/component-waiver limitations are accepted or repaired.
