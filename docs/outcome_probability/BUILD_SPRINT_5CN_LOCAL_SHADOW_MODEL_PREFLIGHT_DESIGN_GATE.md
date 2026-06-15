# Sprint 5CN: Local Shadow Model Preflight Design Gate

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_LOCAL_SHADOW_MODEL_PREFLIGHT_ONLY`

Sprint type: `DESIGN_GATE_NO_MODEL_TRAINING_NO_RELEASE`

## 1. Scope

Sprint 5CN decides whether Sprint 5CO may run a local-only aggregate shadow threshold model evaluation. This sprint did not train models, fit calibration, score current players, create probabilities, create exact display percentages, create coarse display bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie files, edit `data/`, commit `local_exports/`, create production model artifacts, push, or deploy.

## 2. Evidence Read

5CN inspected:

- `docs/outcome_probability/BUILD_SPRINT_5CK_R_2019_QB_SOURCE_TARGET_POSITION_MISMATCH_BLOCKER_RESOLUTION.md`
- `docs/outcome_probability/BUILD_SPRINT_5CK_R2_CONSOLIDATED_2010_2019_HISTORICAL_MODEL_READINESS_REAUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5CL_LOCAL_ONLY_THRESHOLD_HEAD_SUPPORT_EVALUATION.md`
- `docs/outcome_probability/BUILD_SPRINT_5CM_PHASE_4_EVALUATION_AND_DISPLAY_GATE_CONTRACT_PLAN.md`
- `local_exports/outcome_probability/sprint_5cl_threshold_head_support_evaluation/threshold_head_support_evaluation.csv`
- existing local-only historical feature snapshot schema examples

No new local export was required for 5CN.

## 3. Head Eligibility

Eligible heads for 5CO local shadow evaluation:

| Head | Position | Positive labels | Negative labels | Supported seasons | Rationale |
| --- | --- | ---: | ---: | ---: | --- |
| `same_year_qb_t12` | QB | 112 | 441 | 10 | GREEN support, only 1 sparse season |
| `same_year_qb_t18` | QB | 168 | 385 | 10 | GREEN support, no sparse seasons |
| `same_year_qb_t24` | QB | 216 | 337 | 10 | GREEN support, no sparse seasons |
| `same_year_rb_t12` | RB | 106 | 883 | 10 | GREEN support, 2 sparse seasons |
| `same_year_rb_t24` | RB | 210 | 779 | 10 | GREEN support, no sparse seasons |
| `same_year_rb_t36` | RB | 305 | 684 | 10 | GREEN support, no sparse seasons |
| `same_year_rb_t48` | RB | 396 | 593 | 10 | GREEN support, no sparse seasons |
| `same_year_wr_t12` | WR | 115 | 1317 | 10 | GREEN support, no sparse seasons |
| `same_year_wr_t24` | WR | 221 | 1211 | 10 | GREEN support, no sparse seasons |
| `same_year_wr_t36` | WR | 330 | 1102 | 10 | GREEN support, no sparse seasons |
| `same_year_wr_t48` | WR | 433 | 999 | 10 | GREEN support, no sparse seasons |
| `same_year_te_t12` | TE | 113 | 714 | 10 | GREEN support, no sparse seasons |
| `same_year_te_t18` | TE | 162 | 665 | 10 | GREEN support, no sparse seasons |
| `same_year_te_t24` | TE | 210 | 617 | 10 | GREEN support, no sparse seasons |

Weak/constrained heads, not approved for 5CO modeling:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

Blocked heads: none from the evaluated 5CL candidate set.

## 4. Time-Aware Split

5CO must use time-aware rolling holdout evaluation only. Random splits are not allowed.

Approved split design:

| Fold | Training target seasons | Holdout target season |
| --- | --- | ---: |
| 1 | 2010-2015 | 2016 |
| 2 | 2010-2016 | 2017 |
| 3 | 2010-2017 | 2018 |
| 4 | 2010-2018 | 2019 |

The 5CK-R accepted Taysom Hill exclusion must remain excluded. No same-season target final stats may be used as features.

## 5. Feature Allowlist

5CO may use only these approved source-safe prior completed-season features from the historical feature snapshot JSON:

- `position`
- `prior_completed_season_games`
- `prior_completed_season_games_active`
- `prior_completed_season_games_played`
- `prior_completed_season_passing_yards`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_rushing_yards`
- `prior_season_nwr_finish_rank`
- `prior_season_nwr_ppg`

Model design note: `position` may be used only as a categorical identity/context feature. In practice 5CO should evaluate heads within a single position, so position is expected to be constant inside each head.

## 6. Forbidden Fields

5CO must reconfirm that these fields are not used as features:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA fields
- `wopr`
- `racr`
- `pacr`
- `dakota`
- target-share or air-yard-share style fields
- market ranks
- ADP
- projections
- public rankings
- consensus
- trade values/calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- target-year outcome labels or same-season final stats as preseason features
- label supplement sources as prediction features

## 7. Baselines And Metrics

5CO may compare only simple, auditable local shadow methods:

- holdout base-rate baseline from the training fold
- source-safe prior-rank baseline
- source-safe prior-PPG baseline
- a low-complexity logistic model if available from installed libraries or a small in-script implementation

5CO may report aggregate metrics by head and holdout season only:

- train and holdout support counts
- positives and negatives
- base-rate baseline comparison
- AUC where computable
- PR-AUC where computable
- Brier score where computable
- log loss where computable
- calibration-bin aggregate summaries where computable

If a metric cannot be computed due to one-class holdout data or support limits, 5CO must document the limitation rather than forcing a number.

## 8. Output Contract

5CO local-only outputs may be written only under:

`local_exports/outcome_probability/sprint_5co_local_only_aggregate_shadow_model_evaluation/`

5CO must not write:

- row-level/player-level predicted probability CSVs
- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable probability, band, or status outputs
- production model artifacts
- pickled promoted models
- ranking/sorting outputs
- hidden sort keys
- app loader or Streamlit files

Aggregate model coefficients or feature-importance diagnostics may be written only if they are local-only, source-safe, and not player-level.

## 9. Verdict

5CN verdict: GREEN.

5CO is approved to run next as local-only aggregate shadow model evaluation for the 14 eligible heads above.

This approval does not approve production modeling, current-player scoring, display, exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, or promoted artifacts.

## 10. Checks

Checks run:

- packet preflight path/branch/status/log check passed
- `git diff --check` passed

No Python files changed in 5CN, so `python -m py_compile`, Ruff, and pytest are not required.
