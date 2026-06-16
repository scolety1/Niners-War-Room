# Build Sprint 4B - v0 Quality Audit

Status: `READY_AFTER_BUCKET_COLLAPSE`

Sprint 4B audits the limited Sprint 4 truth-set v0 base-rate scaffold before any calibrated model work. It does not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, or deploy.

## Inputs

Sprint 4B reads only the local Sprint 4 outputs under:

`local_exports/outcome_probability/sprint_4_v0_base_rates/`

Important Sprint 4 context:

- Scope: `limited_truth_set_v0`
- Component waiver: `truth_set_v0_component_waiver_v1`
- Bucket rows: 530
- Parent priors: 80
- Player-season labels emitted internally: 166
- Next-year starter labels: 96 observed, 70 censored/null excluded

## Outputs

Sprint 4B writes only to:

`local_exports/outcome_probability/sprint_4b_v0_quality_audit/`

Created outputs:

- `v0_bucket_reliability_by_family.csv`
- `v0_outcome_support.csv`
- `v0_parent_fallback_audit.csv`
- `v0_component_waiver_impact.csv`
- `v0_bucket_collapse_recommendations.csv`
- `v0_benchmark_readiness_verdict.csv`
- `README_SPRINT_4B.md`

## Reliability Summary

Reliability by bucket count:

- `C`: 30
- `D`: 484
- `UNPUBLISHABLE`: 16

No `A` or `B` buckets exist. Most buckets are sparse and parent-heavy.

Reliability by bucket family:

- `position`: 10 C, 30 D
- `position_cohort`: 10 C, 30 D
- `age_band`: 10 C, 30 D, but all values are `age_unavailable`
- `prior_finish_tier`: 88 D, 2 UNPUBLISHABLE
- `trailing_ppg_tier`: 160 D, 10 UNPUBLISHABLE
- `games_played_tier`: 146 D, 4 UNPUBLISHABLE

## Parent Fallback Summary

Parent fallback audit:

- parent-dominated buckets: 414
- no-child-signal buckets: 16
- meaningful child-signal buckets: 100

This means most child buckets should not be used directly. The useful v0 benchmark layer is the low-dimensional position / position-cohort view plus parent-smoothed audit context.

## Outcome Support

Same-year outcomes are fully observed in the limited truth set, but the truth-set appears enriched:

- `same_year_starter`: 166 observed, 166 successes in position buckets
- `same_year_useful`: 166 observed, 166 successes in position buckets
- `same_year_replacement_or_bust`: 166 observed, 0 successes in position buckets
- `same_year_difference_maker`: 166 observed, 148 successes in position buckets

This saturation is not credible as a full-NFL calibrated prior. It can still be useful as an internal benchmark against the truth-set universe.

`next_year_starter` is weaker:

- 96 observed
- 70 censored/null excluded
- 16 UNPUBLISHABLE buckets

Recommendation: keep `next_year_starter` as research-only until more years or broader rows exist.

## Component Waiver Impact

Covered canonical components:

- passing yards, passing TDs, interceptions
- rushing yards, rushing TDs, rushing first downs
- receptions, receiving yards, receiving TDs, receiving first downs
- fumbles lost

Zero-weight/default-safe:

- passing first downs
- sacks suffered
- misc yards

Waived rare nonzero components:

- pass/rush/receiving 2-point conversions
- return yards
- return TDs
- special TDs
- fumble recovery TDs

The waiver is acceptable for internal benchmark only. It should be reviewed or supplemented before app use or calibrated model work.

## Recommendations

Bucket families to keep:

- `position`
- `position_cohort`

Bucket families to collapse:

- `prior_finish_tier`
- `trailing_ppg_tier`
- `games_played_tier`

Collapse these to parent priors unless `n_raw >= 25`.

Bucket families to disable:

- `age_band`

Age-band currently carries only `age_unavailable`, so it should be disabled until age/date-of-birth coverage is registered.

Outcomes to keep for internal benchmark:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Outcome to disable for Sprint 5 calibration:

- `next_year_starter`

Row families to keep:

- `all_player_pre_week1`
- `offseason_carryover`

Row families to disable:

- `rookie_post_draft`, until historical draft-capital source registration is complete.

## Verdict

`READY_AFTER_BUCKET_COLLAPSE`

The v0 layer is not ready for calibrated model work. It is good enough for internal benchmark use only after downstream consumers ignore/collapse sparse child buckets and treat same-year truth-set saturation as a sampling limitation.

## Sprint 5 Status

Sprint 5 calibrated model work remains blocked for production/app use.

Recommended next task: build Sprint 4C collapsed benchmark exports that keep only position / position-cohort buckets plus a clear exclusion file for disabled sparse buckets.
