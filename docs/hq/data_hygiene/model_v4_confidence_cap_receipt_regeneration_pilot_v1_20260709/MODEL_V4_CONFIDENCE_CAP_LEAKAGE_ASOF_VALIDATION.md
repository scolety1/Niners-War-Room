# Model v4 Confidence Cap Leakage / As-Of Validation

## Result

`PASS_REVIEW_ONLY_LAGGED_SOURCE`

- Regenerated rows: `5518`
- Source rows: `42933`
- Source decision flag: `partial_v3_lagged_safe`
- Source gate: `review_only_not_model_training_prod`
- Current-board values used as historical inputs: `0`
- Future-known outcome fields used as inputs: `0`
- Formula weights tuned: `0`

The generated confidence cap value is a deterministic component-coverage ratio from lagged partial receipt rows. It is not an accuracy score and is not production/model-use.
