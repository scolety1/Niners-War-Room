# Phase 11F Confidence And Missingness Layer

## Purpose

Phase 11F creates review-only confidence caps from admitted metadata. It does not read player stat JSON, market context, projections, ADP, rankings, or active app surfaces.

## Outputs

- `local_exports\model_v4\current_value\latest\confidence_missingness_review_rows.csv`
- `local_exports\model_v4\current_value\latest\confidence_missingness_receipts.csv`
- `local_exports\model_v4\current_value\latest\confidence_missingness_warnings.csv`

## Source Rules

- Uses only Phase 11A confidence_missingness fields.
- Current prospects come from admitted_prospect_current_feature_matrix.csv.
- Missing evidence creates caps and warnings, never zero, average, or positive evidence.
- Stale-season and lifecycle gaps are warning-driven because those direct fields are not allowed.

## Summary

- Review rows: 686
- NFL player rows: 80
- Current prospect rows: 211
- Historical rookie rows: 395
- Receipt rows: 3430
- Warning rows: 1545
- Market rows used: 0
- Generic JSON rows used: 0

## Confidence Status Counts

| Status | Count |
| --- | ---: |
| capped_review_required | 502 |
| high_confidence_metadata | 3 |
| usable_with_confidence_cap | 181 |
