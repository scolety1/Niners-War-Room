# Final Rookie Model HQ Recommendation

## Verdict

`YELLOW`

## Decision

- 2000-2024 tuning is not safe now.
- 2012-2024 post-draft label-only evaluation is safe for review-only analysis using factual draft
  rows and Outcome V2 labels, but not for model input or app wiring.
- Pre-draft modeling is not safe now because approved historical CFBD identity joins remain `0`.

## Evidence Needed Next

- A label-only 2000-2011 Outcome V2 backfill candidate built from approved nflverse player stats.
- A 2012 overlap parity test against existing Outcome V2 labels.
- A historical CFBD identity bridge with stable CFBD IDs, school timelines, transfer handling, and
  human review.
- A separate UDFA/non-drafted source policy before adding non-drafted prospects.

## Recommended Next Branch

`work/rookie-model-outcome-v2-2000-2011-label-only-backfill-candidate-20260630`

The next lane should still avoid tuning, rankings, model outputs, and app wiring.
