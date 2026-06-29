# Rookie Outcome Target And Label Specification - 2026-06-29

## Status

Specification only.

No rookie labels, rookie probabilities, model scores, or Rankings columns are created by this lane.

## Target Families

Future rookie outcome work should support these target families only after data and approval gates pass:

- Rookie-year threshold outcome
- Year-2 threshold outcome
- Within-first-3-years threshold outcome
- Within-first-5-years threshold outcome

`Within-first-N-years` means the player hits the threshold at least once during that window.

## Position Thresholds

| Position | Candidate Thresholds |
|---|---|
| QB | T6, T12 |
| RB | T6, T12, T24, T36 |
| WR | T6, T12, T24, T36 |
| TE | T6, T12 |

The final threshold set should be chosen only after sample-size and calibration review.

## Scoring Target

The target should match the league scoring as closely as possible:

- 1QB
- non-PPR
- pass yards: 1 per 30
- pass TD: 3
- interception: -1
- rush/receiving yards: 1 per 10
- rush/receiving TD: 4
- rush/receiving first down: 0.4
- return yards: 1 per 30 if available
- return TD: 4
- 2-point conversion: 2
- fumble lost: -1

## First-Down Scoring Policy

If historical first-down data is complete and approved, labels may be exact.

If first-down data is unavailable or incomplete:

- do not claim exact scoring
- label the artifact as a scoring approximation
- document expected scoring error
- keep exact first-down-adjusted labels blocked

## Rookie / Prospect Eligibility

Eligible rows for a future active build must have:

- approved player identity bridge from prospect/college to NFL player
- approved rookie class or draft year
- approved NFL entry status
- approved position
- enough post-entry NFL seasons for the requested horizon
- explicit censoring status for immature classes

Rookie/prospect rows with missing identity or missing draft year must show `Not enough information`, never `0%`.

## Draft-Year Alignment

For historical labels:

- rookie-year means NFL season equal to draft year or first NFL season
- year-2 means one season after rookie year
- first-3-years means rookie year through year 3
- first-5-years means rookie year through year 5

Future work must explicitly handle:

- redshirt/inactive rookie seasons
- undrafted free agents
- delayed debuts
- position changes
- team changes
- name changes or suffix variations

## College-To-NFL Identity Requirements

Before a row can be used in labels or features:

- CFBD identity must be human-approved or come from a separately approved source-truth identity artifact
- NWR/Sleeper/NFL player ID bridge must be explicit
- same-name conflicts must be resolved
- transfer/team timeline must be reviewed when production context is used
- production context must belong to the correct player-season

High-confidence automated matches are review candidates, not approvals.

## Draft Capital Requirements

A future build needs approved, tracked fields for:

- NFL draft year
- NFL draft round
- NFL overall pick
- NFL team drafted by
- undrafted free agent status if applicable
- rookie class year
- position at draft

Draft capital should be treated as factual NFL entry context after identity validation. It must not be market, ADP, or DynastyProcess-derived value.

## Missing Data Behavior

Missing means `Not enough information`.

Missing data must not become:

- 0%
- false
- low risk
- healthy
- average
- clean
- bad outcome

## Leakage Rules

Future labels may use post-entry NFL outcomes only as labels or validation truth, never as pre-draft features.

Future features must be as-of safe:

- pre-draft model features may not use rookie-year NFL production
- draft capital may be used only after the NFL Draft and only if the target use is post-draft rookie evaluation
- market, ADP, DynastyProcess, vendor data, and Gmail evidence are not model truth
- CFBD remains blocked until approval

## Validation Requirements

Before any rookie outcome model can be active, future work must produce:

- row-level label audit
- source and policy audit
- sample-size by position and horizon
- censoring audit for immature classes
- leakage audit
- missingness audit
- calibration metrics
- Brier score where probability outputs are proposed
- reliability buckets
- baseline comparison against draft-capital-only and simple hybrid baselines
- explicit app/Rankings display gate

If validation is weak, the correct status is blocked, not partial fake output.
