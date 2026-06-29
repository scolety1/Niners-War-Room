# Gate E Model R&D Plan - 2026-06-30

## Allowed Inputs

- `draft_round`
- `draft_pick`
- `draft_capital_bucket`
- `draft_year`
- `rookie_class_year`
- `position`

Historical labels are targets only, never input features.

## Targets

- rookie-year T12/T24/T36 where applicable
- year-2 T12/T24/T36 where applicable
- first-3-year T12/T24/T36 where windows are complete
- first-5-year T12/T24/T36 where windows are complete

## No-Leakage Split

Each target uses earlier rookie classes for empirical rates and the latest
three eligible classes as validation. First-3-year and first-5-year targets
exclude censored classes.

## Baseline

Empirical hit-rate tables by `position + draft_capital_bucket`, with fallback
to position or global target rate when training samples are sparse.

## Validation Bar

- validation rows >= 50
- empirical Brier score improves over global-rate baseline
- all artifacts remain review-only with model/training flags closed
