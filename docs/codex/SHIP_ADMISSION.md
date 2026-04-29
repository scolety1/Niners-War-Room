# Ship Admission

Use this with SHIP_SCORECARD.md before giving the ship meaningful autonomous runtime.

## Decision

Decision: REVIEW

Reason: Auto-backfilled from fleet config. A human should confirm the scorecard before enforcing admission gates.

Next action: Fill any project-specific user job, evaluator, and usefulness details that the backfill could not infer.

## Required Checks

- [x] SHIP_SCORECARD.md has a score and no checked red flags.
- [x] USER_JOB.md names the primary user and recurring job.
- [x] EVALUATORS.md defines a local build, visual, product, data, or copy check.
- [ ] Product owner has confirmed this is still worth autonomous runtime.

## Red Flag Notes

If any scorecard red flag applies, explain the redesign or approval here before launching long runs.
