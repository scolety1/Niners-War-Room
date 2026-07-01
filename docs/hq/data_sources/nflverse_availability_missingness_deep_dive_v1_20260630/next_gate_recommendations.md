# Next Gate Recommendations

Verdict: `YELLOW_NEXT_GATE_DEFINED_NO_APPROVAL`

## Recommended Next Lane

Run a point-in-time availability denominator replay and game-status feasibility
lane before any experiment, model, training, source-truth, rank, hidden-sort,
recommendation, trade-value, or pick-value proposal.

## Required Proof For Absence Or Missed Games

1. Define prediction anchors and historical as-of timestamps.
2. Build point-in-time roster, weekly roster, schedule, snap, stat, and injury
   source snapshots.
3. Define a factual game-status hierarchy.
4. Preserve bye, postponed, canceled, postseason, and schedule exception states.
5. Preserve identity gating and exclude unresolved identity rows.
6. Keep missing snap and stat rows separate from zero usage.
7. Keep missing injury report rows separate from healthy or clean states.
8. Produce row-level censoring reasons.
9. Compare against evaluation labels without making labels input features.
10. Run leakage and label-parity diagnostics.

## Experiment Gate

The current packet has `0` experiment-safe fields. A future experiment-only lane
must still keep all of the following blocked until explicitly approved:

- production model use
- training input
- source truth
- app behavior
- ranking and hidden sort
- recommendations
- trade value
- pick value
- health or medical inference

## Current Safe Use

Continue to use denominator fields only as display/review context where existing
display lanes require:

- safe identity
- `review_required=false`
- `denominator_status=SAFE_NOW_DISPLAY_ONLY`
- schema-approved display-only fields
- missing values as `Not enough information`

`games_missed_while_rostered` remains blocked.
