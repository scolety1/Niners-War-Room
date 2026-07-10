# Sparse-History Breakout Red Team / Rookie-Young Player Model Design V1

## Verdict

`GREEN_SPARSE_HISTORY_BREAKOUT_DESIGN_READY_FOR_RULE_TEST`

## Scope

This is a review-only design and red-team lane. It did not change production rankings, app/runtime/model behavior, source promotion, push/merge state, canonical `local_exports`, ranking simulation, or formula weights.

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`.

Prior addendum commit verified: `8e31c89aee7bc2598046206dd0ec8336dce1c248`.

## Sparse-History Population

Rows analyzed: `4382`.

Startable hits inside sparse-history population: `528`.

Reference false negatives inside sparse-history population: `282`.

Reference false positives inside sparse-history population: `302`.

## Top Sparse-History Breakout Characteristics

starter/depth signal; snap/depth role-promotion signal; availability rebound / clean-report context; expected fantasy opportunity present; NGS context present

## Top Sparse-History False-Positive Traps

injury/availability caveat (219); sparse production without role promotion (132); young player with no snap/depth growth (67); low snap / low depth signal (44); draft capital without role (15)

## Design Decision

A future `Sparse-History Breakout Candidate Rule Test V1` is justified as a bounded review-only lane. The rule test should be predeclared, position-specific, and limited to the modules in the feature policy matrix. It must not become production ranking logic, a broad Gauntlet, or dynamic tuning.

## Ranking Simulation Decision

Review-only ranking simulation remains not justified.

## Source Joins

Sidecar/context joins used for design: `{'snap_depth': 5518, 'injury': 5518, 'rookie_draft': 5518, 'ffopportunity': 1740, 'ngs': 944}`.
