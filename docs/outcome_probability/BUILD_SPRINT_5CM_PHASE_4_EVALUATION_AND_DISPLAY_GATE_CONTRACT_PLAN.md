# Sprint 5CM: Phase 4 Evaluation And Display Gate Contract Plan

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_DOCS_ONLY_PLANNING_GATE_RELEASE_BLOCKED`

Sprint type: `PHASE_4_PLANNING_ONLY_NO_IMPLEMENTATION`

## 1. Scope

Sprint 5CM creates the planning-only gate contract for future Outcome Column evaluation and display consideration after the 2010-2019 historical package foundation, 5CK-R2 consolidated readiness re-audit, and 5CL support-count evaluation.

This sprint did not implement model training, score players, create probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie files, edit `data/`, edit raw source data, or create promoted artifacts.

No local-only export is required for 5CM.

## 2. Historical Support Summary

The current internal-only historical foundation covers target seasons 2010 through 2019 using completed prior-season sources only:

| Package | Target seasons | Feature rows | Label rows | Gate status |
| --- | --- | ---: | ---: | --- |
| 5CI / 5CJ | 2010-2011 | 749 | 749 | audited GREEN |
| 5CF / 5CG | 2012-2013 | 754 | 754 | audited GREEN |
| 5CC / 5CD | 2014-2015 | 760 | 760 | audited GREEN |
| 5BZ / 5CA | 2016-2017 | 778 | 778 | audited GREEN |
| 5BV / 5BW | 2018-2019 | 760 | 760 | audited GREEN with later 5CK-R accepted exclusion |
| 5CK-R2 | 2010-2019 consolidated | 3801 | 3801 | readiness GREEN |

5CK-R2 accepted exactly one excluded non-missing-label blocker:

- `00-0033357` Taysom Hill, 2018 QB source to 2019 TE target, `blocked_source_target_position_mismatch`

That row remains excluded from usable feature/label rows.

## 3. Threshold Support Summary

5CL evaluated 19 candidate heads using counts only:

| Support label | Heads | Meaning |
| --- | ---: | --- |
| GREEN | 14 | enough count support to propose a future local shadow modeling evaluation only |
| YELLOW | 5 | constrained support; needs HQ limits before any shadow modeling proposal |
| RED | 0 | no evaluated head was count-blocked at 5CL |

GREEN support-only heads:

- `same_year_qb_t12`
- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_rb_t12`
- `same_year_rb_t24`
- `same_year_rb_t36`
- `same_year_rb_t48`
- `same_year_wr_t12`
- `same_year_wr_t24`
- `same_year_wr_t36`
- `same_year_wr_t48`
- `same_year_te_t12`
- `same_year_te_t18`
- `same_year_te_t24`

YELLOW constrained heads:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

These are internal support labels only. They are not app-facing states, probability bands, ranking signals, hidden sort keys, or release claims.

## 4. Local Shadow Modeling Gate Prerequisites

A later HQ prompt may propose local shadow modeling only after all of the following are true:

1. The exact approved head list is named before any modeling script is run.
2. The training, validation, and test split contract is documented before modeling.
3. The 5CK-R accepted Taysom Hill exclusion is preserved unless HQ explicitly approves a different multi-position policy.
4. All source rows remain local-only and non-app-readable.
5. No rookie rows are scored through veteran heads.
6. No current-season or same-season final stats are used as preseason features.
7. Forbidden inputs remain quarantined, including ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, and label supplement sources as prediction features.
8. The future sprint states explicitly whether it is local shadow modeling only, not display or release.

5CM approves a future local shadow modeling proposal as the next research topic. It does not approve running that modeling.

## 5. Internal Evaluation Metrics

If HQ later approves local shadow modeling, allowed internal metrics may include:

- positive and negative support counts
- train/validation/test row counts
- head-level confusion counts at predeclared internal decision thresholds
- Brier score for internal calibration assessment
- log loss for internal probability quality assessment
- calibration bucket counts using predeclared bins
- monotonicity checks for ordered threshold heads
- position-level and head-level stability diagnostics

These metrics must remain internal-only. They must not be converted into app-readable probability, band, ranking, sorting, or display artifacts without a later display-contract approval.

## 6. Calibration Audit Requirements

Any future model output must pass a separate calibration audit before display can be considered.

Required calibration gates:

- validation and test splits must be locked before training
- calibration metrics must be reported by head and position
- calibration bins must have minimum holdout support
- sparse heads must abstain rather than emit unstable values
- exact percentages must stay blocked unless calibration is strong and repeatable
- coarse bands must stay blocked unless HQ approves a separate band proposal
- no calibration result may be backfilled into app-readable output paths

## 7. Sanity Audit Requirements

Any future model output must pass player-level sanity review before display can be considered.

Required review slices:

- QB, RB, WR, and TE separately
- high prior-year scorers
- low prior-year scorers
- injury-affected prior-year rows
- team-change rows
- position-transition rows
- multi-role players
- low-games prior-year rows
- players near threshold boundaries
- historical misses and outliers

The Taysom Hill accepted exclusion shows that multi-position rows need explicit policy before modeling or display.

## 8. Human Review Packet Requirements

Before any display proposal, HQ must review a human packet containing:

- model scope and exact head list
- training and holdout split definitions
- feature allowlist
- forbidden feature scan
- calibration results
- abstention policy
- player-level sanity examples
- known failure modes
- rollback plan
- app-display contract draft

The packet must avoid player-facing exact percentages or coarse bands unless the specific sprint is approved to propose them.

## 9. Coarse Band Proposal Conditions

Coarse bands remain blocked today.

Coarse bands could only be proposed to HQ if all of the following later become true:

- a local shadow model is approved and completed
- calibration is stable on validation and test
- abstention rules prevent sparse or unstable heads from displaying
- band labels are defined as product copy, not numeric substitutes
- app-readable band artifacts are separately reviewed
- no rankings/sorting or hidden sort key can be derived from the bands
- rollback and quarantine procedures are documented

5CM does not approve coarse bands.

## 10. Exact Percentage Proposal Conditions

Exact percentages remain blocked today.

Exact percentages could only be proposed to HQ if all of the following later become true:

- calibration is strong and repeatable by head and position
- holdout reliability remains stable across more than one evaluation slice
- player-level sanity review finds no misleading user-facing cases
- exact wording explains uncertainty without overclaiming
- app-readable probability artifacts are separately reviewed
- ranking/sorting and hidden-key use remains blocked unless separately approved

5CM does not approve exact percentages.

## 11. App Display Contract Requirements

Before app wiring, HQ must approve a separate display contract that defines:

- exact allowed app-readable files
- exact allowed app fields
- allowed non-numeric status values
- whether any head may abstain
- app copy for unavailable or blocked values
- explicit prohibition on ranking/sorting unless separately approved
- explicit prohibition on hidden sort keys unless separately approved
- rollback path for removing the column or display state

Existing status-only Outcome Model Status copy remains safe. 5CM creates no app-readable status table and does not change app files.

## 12. Rankings, Sorting, And Hidden-Key Proof

Any future display implementation must prove:

- no outcome probability is used in ranking
- no coarse band is used in ranking
- no status label is used as a hidden sort key
- no app loader imports local-only research exports
- no promoted artifact is created by the display sprint
- no player-card path displays unapproved output

5CM makes no ranking, sorting, hidden-key, or app-loader changes.

## 13. Rollback And Quarantine Plan

Future work must preserve:

- local-only research outputs under `local_exports/outcome_probability/`
- no commits of `local_exports/`
- no commits of `data/`
- no production artifact promotion without HQ approval
- a clear rollback path for deleting app-readable artifacts if a later sprint creates any under approval
- a clear rollback path for removing any display copy if a later app sprint is approved

## 14. User-Facing Copy Review

Before any launch, HQ must separately review user-facing copy for:

- uncertainty language
- abstention wording
- no overclaiming
- no implied rankings
- no implied certainty
- no conversion of internal support labels into user-facing performance claims

## 15. Remaining Active Blockers

The following remain blocked after 5CM:

- model training
- player probabilities
- exact percentages
- coarse bands
- app-readable probability outputs
- app-readable band outputs
- app-readable status tables created by Outcome research sprints
- app wiring
- rankings/sorting
- hidden sort keys
- promoted artifacts
- rookie framework changes
- scoring rookies through veteran heads
- `data/` commits
- `local_exports/` commits
- push/deploy

## 16. Recommendation

5CM recommendation: GREEN for docs-only planning.

Future local shadow modeling is approved to propose next, not run. The next safe sprint should be an HQ-scoped local shadow modeling proposal that names the exact heads, split policy, allowed metrics, and quarantine rules before any model code executes.

## 17. Checks

Checks run:

- `git diff --check` passed

No script changed in 5CM, so `python -m py_compile`, Ruff, and pytest are not required.
