# Rookie Production-Candidate Promotion Plan - 2026-06-13

## Status

This is a production-candidate plan only. It is not production promotion and does not approve app wiring, production ranking replacement, private-score changes, probabilities, bands, outcome columns, or veteran outcome-head usage.

## Stage B Decision

Stage B creates:

- a tracked production-candidate contract;
- a tracked local-only candidate builder;
- tracked tests for the candidate builder;
- local-only production-candidate exports.

The candidate exports remain `production_candidate_only=yes`, `app_read_allowed=no`, and `probabilities_created=no`.

## Candidate Export Path

Local-only exports are written to:

`local_exports/model_v4/rookie_framework_v02/production_candidate_v03/`

These files must not be committed.

## Promotion Preconditions

Before any future production promotion proposal can become implementation work, all of the following must be true:

1. Stage C adversarial audit is GREEN.
2. Stage D rollback and promotion proposal is GREEN.
3. Stage E final approval checkpoint is GREEN.
4. HQ explicitly approves a separate implementation task.
5. The implementation task names exact files, artifacts, tests, app behavior, rollback procedure, and signoff.

## Required Preservation

Any future production proposal must preserve:

- `1.03` empty if unsupported;
- all `1.04` manual warnings;
- source confidence;
- hard caps;
- soft flags;
- manual-review flags;
- remaining gaps;
- prohibited-source warnings;
- source-conflict status;
- no app-read marker until separately approved;
- no probabilities or bands.

## Current Expected Blockers

Current blockers are expected to remain visible:

- unresolved `1.03` premium bar;
- Jordyn Tyson injury review;
- premium WR route/separation/press/YAC and target-rate gaps;
- RB pass-protection/contact/fumble/first-down/goal-line/injury gaps;
- low source confidence for most `5.04` watchlist rows;
- no Round 2 WR/TE/QB rows;
- no current QB exception;
- TE exceptions remain manual and discounted.

## Rollback Plan For Future Implementation

If a later approved production implementation fails validation:

1. Stop before app wiring.
2. Do not commit production ranking changes.
3. Delete or quarantine generated local candidate outputs.
4. Restore the last known committed rookie docs/scripts/tests state.
5. Write a checkpoint blocker doc that names the failed gate, failed command, and affected files.

If a later implementation is committed and then rejected:

1. Revert only the explicitly approved implementation commit.
2. Preserve review/shadow/candidate docs unless HQ instructs otherwise.
3. Rebuild review, shadow, and candidate local exports.
4. Re-run direct harnesses and strict builds.
5. Confirm `data/` and `local_exports/` remain uncommitted.

## Recommendation For Stage C

Proceed to Stage C only after strict candidate export validation passes.

Stage C should adversarially audit whether the candidate contract/export preserved source safety, avoided market/rank/projection contamination, kept `1.03` honest, kept `1.04` warnings visible, and remained non-app/non-production.
