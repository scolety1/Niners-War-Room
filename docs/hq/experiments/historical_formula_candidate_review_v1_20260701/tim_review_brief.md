# Tim Review Brief

`usage_opportunity_volume` is a strong review-only candidate, not a production formula.

What improved:

- Validation MAE improved by `-2.036621`.
- Holdout MAE improved by `-1.646492`.
- All holdout positions and both holdout seasons improved MAE.

What stayed flat:

- Aggregate holdout startable precision stayed flat.

Main risks:

- Bucket-level Top-N tradeoffs remain.
- Largest regression rows need human inspection.
- The formula is still only V3 historical evidence.

Look first at `candidate_decision_card.md`, then `largest_error_regressions_sample.csv`.

Exact next decision: decide whether to send the candidate to a separate human-approved deeper review lane, not production.
