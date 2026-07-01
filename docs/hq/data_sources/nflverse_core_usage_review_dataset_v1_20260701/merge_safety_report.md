# Merge Safety Report

This packet is docs/CSV/Parquet review-only evidence. It does not change runtime behavior.

## Changed Path Scope

`docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/`

## Not Changed

- App pages.
- Model/rank/source-truth code.
- Latest candidate/latest approved pointers.
- Protected board/rank/tier artifacts.
- Runtime JSON.
- Raw/shared/cache/local export/secret files.

## Merge Caveat

If merged, downstream lanes may consume this only as a review-only data artifact. It does not approve production model/training/source-truth/rank/app use.
