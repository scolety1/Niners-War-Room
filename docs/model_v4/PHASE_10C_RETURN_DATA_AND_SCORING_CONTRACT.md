# Phase 10C Return Data And Scoring Contract

Generated: 2026-05-17

## Scope

Phase 10C canonicalized the user-provided 2024 and 2025 RotoWire kick-return
and punt-return exports, then patched the official LVE scoring constants for
return scoring support.

This phase did not change dynasty weights, active rankings, My Team, War Board,
or readiness gates.

## Raw Inputs

Raw exports remain preserved unchanged under:

- `local_exports/model_v4/raw_user_exports/rotowire_manual/2024/returns/`
- `local_exports/model_v4/raw_user_exports/rotowire_manual/2025/returns/`

Source validation notes:

- 2025 kick returns required shifted-header inference.
- 2024 punt returns had one repeated header row removed.
- No exact duplicate rows were removed.
- No malformed rows were removed.
- No numeric issue rows were found.

## Outputs

Return canonicalization outputs:

- `local_exports/model_v4/returns/latest/canonical_return_stats.csv`
- `local_exports/model_v4/returns/latest/return_canonicalization_validation.csv`
- `local_exports/model_v4/returns/latest/return_scoring_receipts.csv`
- `local_exports/model_v4/returns/latest/return_source_coverage.csv`
- `local_exports/model_v4/returns/latest/return_canonicalization_summary.csv`

Generated counts:

| Output | Rows |
| --- | ---: |
| Canonical return rows | 302 |
| Validation files | 4 |
| Receipt rows | 302 |
| Coverage rows | 302 |
| Missing join rows | 53 |
| Ambiguous join rows | 8 |

Source totals:

| Metric | Value |
| --- | ---: |
| Return yards | 87,959 |
| Return TDs | 34 |
| LVE return scoring points if used | 3,067.98 |

## Scoring Contract

Official scoring constants now include:

| Event | Points |
| --- | ---: |
| Return yards | 1 per 30 yards |
| Return TD | 4 |

The shared `LVE_SCORING` config was patched with:

- `return_yard = 1 / 30`
- `return_td = 4`

The weekly LVE recompute helper now supports `return_yards` and `return_tds`.
If total return fields are blank, it can sum kick-return and punt-return fields.

## Receipt Treatment

Return receipts expose:

- raw kick/punt return fields
- normalized kick/punt return fields
- total return yards
- total return TDs
- LVE return scoring points
- scoring constants used
- cleanup warnings

Return role label:

`small_direct_return_scoring_evidence_not_talent_signal`

This means return production is direct scoring support only. It must not become a
major talent signal or hidden dynasty-value weight.

## Safety Confirmations

- Raw return exports preserved unchanged.
- Active app rankings unchanged.
- Active My Team unchanged.
- Active War Board unchanged.
- No readiness gates unlocked.
- No formula weights changed.
- Return evidence remains separate from private football talent value.

## Validation

Focused tests passed:

```text
tests/test_model_v4_return_canonicalization_service.py
tests/test_lve_scoring_derivation_service.py
tests/test_public_source_import_service.py
tests/test_model_v4_rotowire_source_index_service.py
```

Result: 66 passed.

Full validation after header-contract repair:

```text
pytest: 916 passed
ruff check app src scripts tests: passed
```
