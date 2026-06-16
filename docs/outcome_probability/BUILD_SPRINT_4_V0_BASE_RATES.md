# Build Sprint 4 - Limited Truth-Set v0 Base Rates

Status: `limited_internal_v0_created`

Sprint 4 builds a limited internal historical base-rate scaffold from audited legal truth-set rows only. It does not train calibrated models, create player-facing probabilities, create app percentage values, create rankings, push, or deploy.

## Scope

- Scope: `limited_truth_set_v0`
- Component waiver: `truth_set_v0_component_waiver_v1`
- Canonical source: `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`
- Source classification: `production_candidate`
- Source manifest version: `truth_set_v3_source_decisions_v1`
- Label schema version: `nwr_outcome_labels_v1`

These outputs are internal research/base-rate scaffolding only. They are not calibrated probabilities and must not be shown in app outcome percentage columns.

## Included Row Families

- `all_player_pre_week1`
- `offseason_carryover`

Excluded:

- `rookie_post_draft`

`rookie_post_draft` remains excluded until historical draft-capital source registration is complete.

## Included Outcomes

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`
- `next_year_starter`

Future-window labels remain null when incomplete. Null/censored labels are excluded from denominators for that outcome.

## Component Waiver

Covered canonical components:

- passing yards
- passing TDs
- interceptions
- rushing yards
- rushing TDs
- rushing first downs
- receptions
- receiving yards
- receiving TDs
- receiving first downs
- fumbles lost

Zero-weight/default-safe components:

- passing first downs = 0
- sacks suffered = 0
- misc yards = 0

Waived rare nonzero components for limited v0 only:

- pass/rush/receiving 2-point conversions
- return yards
- return TDs
- special TDs
- fumble recovery TDs

Every output row carries `component_waiver_id = truth_set_v0_component_waiver_v1`.

## Bucket Families

The first v0 pass keeps buckets low-dimensional:

- position only
- position x cohort
- position x prior finish tier
- position x trailing PPG tier
- position x games played tier
- position x age band, currently `age_unavailable`

The truth-set source does not provide age in the canonical player-week label file, so age-band buckets are retained as explicit unavailable buckets rather than invented.

## Smoothing

Sprint 4 uses beta-binomial smoothing:

`posterior_mean = (success_raw + prior_alpha) / (n_raw + prior_alpha + prior_beta)`

Parent priors are derived from position/global fallback rates with a fixed prior strength. Outputs include raw counts, raw rates, parent rates, prior alpha/beta, posterior mean, and approximate 80/95 percent intervals.

Raw rates are retained for audit, but downstream use should rely on smoothed posterior values. These are still not calibrated player probabilities.

## Reliability

Reliability flags:

- `A`: n >= 100 and event_count >= 10
- `B`: n >= 50 and event_count >= 5
- `C`: n >= 25
- `D`: sparse / parent-heavy
- `UNPUBLISHABLE`: no observed denominator or too sparse

Sprint 4 output remains internal-only even when a bucket receives a non-UNPUBLISHABLE reliability flag.

## Exports

Outputs are written only under:

`local_exports/outcome_probability/sprint_4_v0_base_rates/`

Created files:

- `base_rate_bucket_results.csv`
- `base_rate_parent_priors.csv`
- `base_rate_input_manifest.csv`
- `base_rate_censoring_report.csv`
- `base_rate_reliability_report.csv`
- `base_rate_leakage_guardrail_report.csv`
- `README_SPRINT_4.md`

## Guardrails

- Imported fantasy totals remain rejected as labels.
- ADP, FantasyPros, public rankings, consensus, startup rankings, trade calculators, public projections, RotoWire projections/rankings/outlooks/values, market rank, league rank, prior fantasy draft history, and legacy `private_score` remain forbidden.
- No app percentage values were created.
- No public/player-facing probabilities were created.
- No rankings were created.

## Sprint 5 Readiness

Sprint 5 calibrated model work remains blocked for production use. A follow-on internal Sprint 4 audit can review these v0 base-rate buckets, component waivers, and sparse bucket behavior. Calibrated probabilities should not begin until the team accepts the limited truth-set scope and decides whether to supplement or waive rare scoring components for broader training.
