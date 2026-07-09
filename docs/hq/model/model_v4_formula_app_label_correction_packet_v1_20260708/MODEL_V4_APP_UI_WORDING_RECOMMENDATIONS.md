# Model v4 App / UI Wording Recommendations

These are recommendations only. This lane does not edit app code.

## Board Header

Recommended:

`Model v4 Review Board`

Alternate if space allows:

`Model v4 Review Board - Rebuild Verified`

Do not use:

- `Production Rankings`
- `Approved Rankings`
- `Active Formula`
- `Final Model`

## Status Badge

Recommended:

`Review-only, rebuild verified`

Alternate compact badge:

`Review board`

## Tooltip / Help Text

Recommended:

`This board exactly rebuilds to the pinned current hash and is visible as the main review board. It remains candidate/review-only: it does not approve production ranking use, source promotion, autonomous recommendations, trade logic, draft logic, or historical accuracy.`

## Board Status Caption

Recommended:

`Hash-rebuild verified current board. Review-only human draft aid. Not production-active or historically accuracy-approved.`

## Data Health Status

Recommended:

`Model v4 board: rebuild verified for current hash; review-only; no production-active approval; historical replay blocked.`

Do not mark it as usable, production-approved, source-truth, or model-use approved because of the rebuild.

## Source Trace Summary

Recommended:

`Current board source chain is recovered and hash-reconciled for the current artifact. Source gates remain unchanged. Current-only receipt recovery does not promote any source or make historical replay decision-date safe.`

## Model Evaluation Page

Recommended:

`Exact current-board rebuild passed. Historical accuracy remains unapproved: the prior current-formula-family proxy had useful signal but did not beat the simple prior-year finish baseline overall.`

## Draft-Day Use Note

Recommended:

`Use as a human review aid only. Do not treat as an autonomous draft recommendation, trade value, cut/keep instruction, buy/sell signal, start/sit signal, or production ranking oracle.`

## Statistic Analysis Wording

Recommended replacement for "approved NWR Score metadata":

`hash-rebuild verified review score metadata`

Recommended replacement for "approved component":

`source-traced review component, where available`

Recommended note:

`Component contribution math remains unavailable unless an approved component receipt artifact reconciles every component to the displayed review score.`
