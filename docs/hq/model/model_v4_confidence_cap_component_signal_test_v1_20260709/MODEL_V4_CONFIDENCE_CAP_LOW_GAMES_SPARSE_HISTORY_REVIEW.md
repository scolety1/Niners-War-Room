# Model v4 Confidence Cap Low-Games / Sparse-History Review

## Summary

- Total tested rows: `5518`
- Sparse-history rows using prior benchmark rule `prior_games < 8`: `1453`
- Low-confidence rows: `28`
- Low-confidence sparse-history rows: `13`
- Low-confidence position distribution: `{'WR': 28}`

## Finding

The regenerated confidence cap does not broadly solve sparse-history uncertainty. It flags only a small WR-only slice. Of those low-confidence WR rows, roughly half are sparse-history rows, and only one low-confidence row became startable.

## Interpretation

This is weak but review-useful as a caution label for a narrow low-coverage WR group. It is not enough to support Formula Gauntlet tournaments, exact replay, or ranking integration.