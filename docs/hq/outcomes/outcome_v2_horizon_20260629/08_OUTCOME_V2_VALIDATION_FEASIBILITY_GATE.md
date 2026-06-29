# Outcome V2 Validation Feasibility Gate - 2026-06-30

## Verdict

`GREEN_PARTIAL_VALIDATION_FEASIBLE`

This gate allows validation only for this-year and next-year fields. It blocks all within-next-5-years fields from app-facing probability work.

## Inputs

Historical label artifacts generated under:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\`

Key coverage:

- Season outcome labels: 3,578
- Anchor horizon labels: 3,569
- Season labels: 2019-2024
- Anchor seasons: 2018-2023
- Complete this-year windows: 2,658
- Complete next-year windows: 1,838
- Complete within-5-year windows: 296
- Right-censored rows: 3,273
- Scoring mode: `exact_verified_first_downs`

## Machine-Readable Matrix

Created:

`docs/hq/outcomes/outcome_v2_horizon_20260629/outcome_v2_validation_feasibility_matrix.csv`

## Feasible Fields

The following 24 this-year / next-year fields have enough complete labels, positive examples, and complete anchor seasons for conservative validation:

- QB T6 This Year
- QB T12 This Year
- QB T6 Next Year
- QB T12 Next Year
- RB T6 This Year
- RB T12 This Year
- RB T24 This Year
- RB T36 This Year
- RB T6 Next Year
- RB T12 Next Year
- RB T24 Next Year
- RB T36 Next Year
- WR T6 This Year
- WR T12 This Year
- WR T24 This Year
- WR T36 This Year
- WR T6 Next Year
- WR T12 Next Year
- WR T24 Next Year
- WR T36 Next Year
- TE T6 This Year
- TE T12 This Year
- TE T6 Next Year
- TE T12 Next Year

## Blocked Fields

All within-next-5-year fields are blocked for app-facing probabilities:

- QB T6/T12 Within Next 5 Years
- RB T6/T12/T24/T36 Within Next 5 Years
- WR T6/T12/T24/T36 Within Next 5 Years
- TE T6/T12 Within Next 5 Years

Reason:

The within-5-year horizon has only 296 complete rows total, only two complete anchor seasons, and heavy right-censoring. This is not enough for app-facing probability display even where a single position-threshold pair has more than 100 complete rows.

## Missing/Censored Policy

Censored or missing horizon windows stay `Not enough information`.

They are not treated as:

- misses
- zero probability
- false
- healthy
- clean
- low risk

## Approved Inputs For Next Phase

Validation may use only factual historical features available from the label factory / historical player-stat panel:

- position
- anchor season
- prior/current anchor-season fantasy points
- prior/current anchor-season position finish
- games played / availability context
- factual usage/production fields if used transparently

Validation may not use:

- DynastyProcess
- ADP
- market values
- CFBD
- Gmail
- vendor projections
- analyst ranks
- true routes / TPRR / YPRR
- injury projections
- medical comeback assumptions
- current Dynasty Rank
- NWR Dynasty Score

## Next Gate

Proceed to probability validation only for fields marked `VALIDATION_FEASIBLE` in the matrix.
