# Truth Set Lab v1 Intake 04: Production Data

## Files

- Raw source: `local_exports/truth_set_lab/v1/source_raw/production_data.csv`
- Clean preview: `local_exports/truth_set_lab/v1/source_clean/production_data.csv`
- Intake summary: `local_exports/truth_set_lab/v1/reports/production_intake_summary.json`
- Intake flags: `local_exports/truth_set_lab/v1/reports/production_intake_flags.csv`
- Strict validation summary: `local_exports/truth_set_lab/v1/reports/production_strict_validation_summary.csv`
- Strict validation flags: `local_exports/truth_set_lab/v1/reports/production_strict_validation_flags.csv`

## Intake Result

Status: `coverage_present_not_model_safe`

The file covers the full 40-player truth set after name normalization. It should not be promoted into production scoring because the CSV is not reliably field-aligned.

## Coverage

- Truth-set rows expected: 40
- Rows present: 40
- Missing truth-set players: 0
- Extra players: 0
- Rows with detected source URLs: 40
- Rows with detected confidence values: 40

## Blocking Quality Issues

The CSV has inconsistent row widths:

| parsed column count | rows |
|---:|---:|
| 23 | 1 |
| 25 | 4 |
| 26 | 20 |
| 27 | 10 |
| 28 | 5 |

Because the header has 27 columns, 30 of 40 rows are malformed by width. The 10 rows that match the header are still not automatically safe because several stat fields appear shifted, contain `?` / `??`, or combine source snippets with football values.

Flag counts:

| flag | count | impact |
|---|---:|---|
| `structured_stat_alignment_untrusted` | 40 | Blocking for model use |
| `malformed_row_width` | 30 | Blocking for model use |
| `uncertain_numeric_marker` | 14 | Blocking for model use |
| `source_text_contains_embedded_urls` | 40 | Review provenance |

## Safe Usage

Safe:

- Use as evidence that the agent attempted to gather production rows for all 40 truth-set players.
- Use the detected player coverage, source URLs, confidence text, and notes for manual review.
- Use this file to guide a corrected re-export request.

Unsafe:

- Do not map the stat columns directly into production features.
- Do not calculate LVE scoring from these parsed columns.
- Do not use these rows to overwrite nflverse production data.
- Do not use the reported confidence values as model confidence.

## Why This Matters

Production data is one of the model's core evidence buckets. A shifted production row can create exactly the kind of nonsense rankings we are trying to eliminate, such as a player being boosted or punished because rushing attempts, targets, first downs, or touchdowns landed in the wrong column.

## Recommended Next Step

Ask the data agent for a corrected production export with strict CSV rules:

1. One row per player.
2. Exact header fields preserved.
3. Every missing numeric field left blank, not omitted.
4. Source name and source URL separated.
5. No pasted URL snippets inside numeric/stat columns.
6. No `?` or `??` values in numeric fields; use blank plus a note instead.

Until a corrected export arrives, production should continue to come from trusted structured sources already in the app, not this file.

## Post-Pro Strict Validator

The app now has a strict production intake validator for future corrected exports.
The current files remain rejected:

- Raw attempted export: header is exact and 40 truth-set players are present, but it still has 30 malformed-width rows, 22 numeric-error rows, 7 uncertain-marker rows, 30 embedded-url rows, and 35 source-separation rows.
- Clean/rejection metadata file: rejected because it is not the strict production schema.

The validator is structural only. It does not import production data into model scoring.
