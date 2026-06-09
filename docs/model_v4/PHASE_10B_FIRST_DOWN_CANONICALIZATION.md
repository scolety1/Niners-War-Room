# Phase 10B First-Down Canonicalization

Generated: 2026-05-17

## Scope

Phase 10B canonicalized the manually collected 2024 and 2025 rushing/receiving first-down exports into review-only evidence tables. Raw exports were preserved unchanged under `local_exports/model_v4/raw_user_exports/rotowire_manual/<season>/first_downs/`.

No formulas, active rankings, My Team, War Board, app promotion surfaces, or readiness gates were changed.

## Outputs

- `local_exports/model_v4/first_downs/latest/canonical_rushing_first_downs.csv`
- `local_exports/model_v4/first_downs/latest/canonical_receiving_first_downs.csv`
- `local_exports/model_v4/first_downs/latest/first_down_canonicalization_validation.csv`
- `local_exports/model_v4/first_downs/latest/first_down_receipts.csv`
- `local_exports/model_v4/first_downs/latest/first_down_source_coverage.csv`
- `local_exports/model_v4/first_downs/latest/first_down_canonicalization_summary.csv`

## Summary

| Metric | Value |
|---|---:|
| Rushing canonical rows | 350 |
| Receiving canonical rows | 575 |
| Receipt rows | 925 |
| Coverage rows | 925 |
| Imported real data rows | 925 |
| Missing join rows | 23 |
| Ambiguous join rows | 29 |
| Model scores changed | False |
| Active rankings overwritten | False |

## Cleanup Results

| Season | Type | Raw Rows | Clean Rows | Imported Real Data | Matched | Missing Join | Ambiguous Join | Cleanup |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 2024 | rushing | 125 | 125 | 125 | 122 | 1 | 2 | missing_header_inferred; missing_join_rows=1; ambiguous_join_rows=2 |
| 2025 | rushing | 225 | 225 | 225 | 212 | 6 | 7 | missing_join_rows=6; ambiguous_join_rows=7 |
| 2024 | receiving | 276 | 275 | 275 | 260 | 6 | 9 | repeated_header_rows_removed=1; missing_join_rows=6; ambiguous_join_rows=9 |
| 2025 | receiving | 350 | 300 | 300 | 279 | 10 | 11 | exact_duplicate_rows_removed=50; missing_join_rows=10; ambiguous_join_rows=11 |

## Join Policy

Rows were joined only when exact normalized player name matched a unique existing RotoWire season/stat-family `basic.csv` row. The first-down exports do not include team or position, so ambiguous traded-player or duplicate-name cases are flagged rather than guessed. Model identity joins are attempted only after the safe RotoWire season/family join supplies position and team context.

## Join Counts

| Join Status | Rows |
|---|---:|
| matched | 873 |
| ambiguous_join | 29 |
| missing_join | 23 |

## Coverage Counts

| Coverage Status | Rows |
|---|---:|
| covered | 873 |
| review_ambiguous_join | 29 |
| review_missing_join | 23 |

## Source Status

Every canonical row is labeled `imported_real_data` because the first-down fields came directly from the provided source exports. Rows with missing or ambiguous joins remain usable as source evidence, but they are review rows until identity is resolved safely.

## Remaining Review Items

- Resolve missing joins where the source player name differs from RotoWire/model identity, for example accented names or players absent from the matching RotoWire family file.
- Resolve ambiguous joins for traded/multi-team rows only if a source-backed aggregate identity rule is added.
- Keep return scoring separate; Phase 10B did not admit return stats into first-down evidence.

## Checks Run

- `pytest tests/test_model_v4_first_down_canonicalization_service.py tests/test_model_v4_rotowire_source_index_service.py`
- Ruff/static check on touched first-down canonicalization and source-index files.
