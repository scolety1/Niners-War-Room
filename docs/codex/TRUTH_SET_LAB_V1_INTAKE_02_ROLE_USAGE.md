# Project Gold Truth Set Lab v1 Intake 02: Role/Usage

Generated: 2026-05-14

## Source Files

- Raw role/usage file: `local_exports/truth_set_lab/v1/source_raw/role_usage_report.csv`
- Clean role/usage preview: `local_exports/truth_set_lab/v1/source_clean/role_usage.csv`
- Aggregate intake summary: `local_exports/truth_set_lab/v1/reports/intake_summary.csv`
- Aggregate intake flags: `local_exports/truth_set_lab/v1/reports/intake_flags.csv`
- Malformed role/usage rows: `local_exports/truth_set_lab/v1/reports/role_usage_malformed_rows.csv`
- Strict validation summary: `local_exports/truth_set_lab/v1/reports/role_usage_strict_validation_summary.csv`
- Strict validation flags: `local_exports/truth_set_lab/v1/reports/role_usage_strict_validation_flags.csv`

## Intake Summary

| category | value |
|---|---:|
| rows | 40 |
| missing truth-set players | 0 |
| extra players | 0 |
| malformed CSV rows | 15 |
| rows with source URL missing | 7 |
| rows with confidence missing | 0 |
| uncertain value rows | 27 |
| WR/TE rows | 27 |
| WR/TE rows with core route metrics | 26 |
| RB rows | 10 |
| RB rows with clean numeric workload shares | 0 |
| QB rows | 3 |

## Findings

- The file covers all 40 truth-set players.
- It contains useful WR/TE preview evidence, especially `routes_run`,
  `target_share`, `targets_per_route_run`, and `yards_per_route_run`.
- 26 of 27 WR/TE rows have the core route/target efficiency fields populated.
- The file is not model-ready:
  - 15 rows have malformed CSV parsing due extra unparsed fields.
  - 27 rows contain `?` uncertainty markers.
  - 9 RB rows put workload text such as rush totals into share/count columns
    instead of clean numeric workload fields.
  - 0 RB rows have clean numeric `rb_carry_share` or `rb_opportunity_share`.
- Most rows are marked as manual extraction. Use this as preview evidence only
  until values are checked against source exports or cleaned source tables.

## Model Use Decision

Do not promote this role/usage file into scoring yet.

The WR/TE route metrics are promising enough to review, but the current CSV shape
and uncertainty markers make it unsafe for automatic normalization. The RB workload
rows need reformatting into clean numeric columns before they can be used.

## Recommended Cleanup Request

Ask the data agent to re-export role/usage with:

- no question marks in numeric fields;
- blank values when unknown;
- numeric counts and shares only in stat columns;
- RB rushing attempts, targets, carries share, opportunity share, red-zone touches,
  and goal-line touches as separate numeric fields;
- notes kept fully quoted or moved to a separate notes file.

## Post-Pro Strict Validator

The app now has a strict role/usage intake validator for future corrected exports.
The current file remains rejected:

- Header mismatch against the strict numeric role/usage schema.
- 40 malformed-width rows under the strict schema.
- 26 rows with uncertainty markers in numeric fields.
- 3 rows with prose in numeric role/workload fields.

The validator is structural only. It does not import role/usage data into model scoring.
