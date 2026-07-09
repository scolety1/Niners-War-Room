# Model v4 Regeneration Output Contract

## Future Artifact Path Pattern

Future regeneration lanes must write only under a review artifact path:

`docs/hq/data_hygiene/model_v4_historical_receipt_regeneration_<family>_v1_YYYYMMDD/`

They must not write into canonical `local_exports`, app paths, runtime paths, source gates, model files, ranking files, or canonical board artifacts.

## Required Files Per Family

Each future family lane must create:

1. `<FAMILY>_REGENERATION_V1_REPORT.md`
2. `<FAMILY>_REGENERATED_RECEIPTS_REVIEW_ONLY.csv`
3. `<FAMILY>_SOURCE_MANIFEST.csv`
4. `<FAMILY>_SCHEMA_VALIDATION.csv`
5. `<FAMILY>_LEAKAGE_ASOF_VALIDATION.csv`
6. `<FAMILY>_IDENTITY_JOIN_VALIDATION.csv`
7. `<FAMILY>_MISSINGNESS_AUDIT.csv`
8. `<FAMILY>_STOP_CONDITION_AUDIT.md`
9. `<FAMILY>_SOURCE_TRACE.md`
10. Any generator script, only under the review artifact folder or a scoped review-safe path.

## Required Output Status

Every regenerated receipt must include:

`allowed_use=review_only_regenerated_not_production_model_use`

Every regenerated receipt must include:

`blocked_use=production_model_use|ranking_integration|formula_activation|source_promotion`

## Required Validation Before Commit

- CSV parse.
- Source hash verification.
- Row count by season and position.
- Unique key check.
- Schema validation.
- Leakage/as-of validation.
- Missingness audit.
- Protected-path scan.
- `git diff --check`.
- `git diff --cached --check`.

## Promotion Boundary

Regenerated receipts are not production inputs. A separate Master HQ review would be required before any broader use.
