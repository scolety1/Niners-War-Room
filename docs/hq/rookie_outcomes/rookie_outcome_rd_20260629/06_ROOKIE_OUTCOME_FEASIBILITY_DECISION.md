# Rookie Outcome Feasibility Decision - 2026-06-29

## Final Feasibility Verdict

`BLOCKED_NEEDS_CFBD_APPROVAL`

## Why This Is The Primary Verdict

The current CFBD identity package is explicitly review-only:

- `approved_by_human=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `review_only=true`

Rookie outcome modeling depends on knowing that the college production and identity rows belong to the correct future NFL player. That gate is not open.

## Secondary Blockers

The lane also remains blocked by:

- draft capital approval
- historical rookie label availability
- identity confidence
- source/data policy gate
- scoring and first-down coverage audit
- censoring-safe horizon labels

## What Can Be Safely Done Now

Safe now:

- review CFBD identity candidates
- review high-confidence exact matches
- repair ambiguous/same-name groups
- design target labels
- design draft-capital artifact schema
- design historical label builder requirements
- audit feature policy
- preserve `Not enough information` for missing data

## What Cannot Be Done Now

Not safe now:

- active rookie T6/T12/T24/T36 probabilities
- Rankings rookie probability columns
- CFBD training truth
- CFBD model input
- rookie model scores
- source-truth promotion
- market/ADP/DynastyProcess input
- vendor/Gmail/news automation
- pick or trade valuation

## Minimum Approval Gate For Future Active Build

A future active rookie outcome build requires:

1. Human-reviewed identity approvals.
2. Draft-capital artifact approved for review use.
3. Historical rookie label artifact approved for validation.
4. Scoring exactness or approximation label.
5. Censoring-safe first-3-year and first-5-year windows.
6. Per-position sample-size audit.
7. Missingness audit.
8. Leakage audit.
9. Baseline comparison.
10. Calibration/Brier validation before any probability display.
11. Separate Rankings integration gate.

## Recommended Next Lane

Recommended next lane:

`CFBD Rookie Identity Human Approval Packet V1`

Goal:

- approve/reject/defer high-confidence CFBD identity rows
- resolve possible/ambiguous groups
- repair malformed prior ambiguous-decision CSV
- keep all approvals review-only until a later source-truth promotion gate

Second recommended lane after identity:

`Rookie Draft Capital Review Artifact V1`

Goal:

- create approved tracked draft-capital review artifact
- cover historical and current rookie classes
- avoid local_exports/raw cache tracking
- preserve model/training blocked flags

## Human Review Checklist

1. Review `rookie_cfbd_readiness_matrix.csv`.
2. Approve/reject/defer the 157 exact-match CFBD candidates.
3. Resolve the 46 possible candidates and 10 ambiguous candidates.
4. Repair or replace the malformed `cfbd_ambiguous_identity_decisions.csv`.
5. Decide which draft-capital source is approved for review artifacts.
6. Decide whether RotoWire-derived historical labels are forbidden entirely or can inform only a migration spec.
7. Confirm whether exact first-down scoring is required before any rookie label build.

## Safe Final State

This lane produces audit/spec/readiness files only.

It does not produce rookie probabilities, model outputs, Rankings columns, or source-truth changes.
