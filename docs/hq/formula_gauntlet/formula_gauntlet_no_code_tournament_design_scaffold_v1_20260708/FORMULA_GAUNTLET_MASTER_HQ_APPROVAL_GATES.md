# Formula Gauntlet Master HQ Approval Gates

## Gate 0: Context Admission

Status: allowed now.

Purpose:

- Admit source-traced packets as review-only context.
- Record caveats.
- Prevent reinvention.

No tournament execution is allowed at this gate.

## Gate 1: Data Hygiene Clearance

Required before any tournament execution.

Master HQ must receive:

- label quality report
- identity join report
- source/use-gate matrix
- missingness report
- leakage/as-of safety report
- blocked input list

## Gate 2: Tournament Contract Approval

Required before running any tournament.

The contract must define:

- tournament class
- seasons
- positions
- eligible universe
- labels
- inputs
- baselines
- metrics
- missingness thresholds
- leakage checks
- output destination
- stop conditions

## Gate 3: Review-Only Execution Approval

Required before scripts or scoring are run.

Execution must be isolated, review-only, and non-production. No output may mutate rankings or app/runtime behavior.

## Gate 4: Advancement Review

Required after tournament results.

Master HQ must decide whether a candidate:

- advances as review-only evidence
- is held for more data
- is rejected
- is blocked by source/data caveats

No candidate can become production-active at this gate.

## Gate 5: Separate Promotion Lane

Required for any future production discussion.

Promotion cannot be bundled with Formula Gauntlet. It requires separate source admission, model review, app/runtime review, ranking review, human approval, and rollback plan.
