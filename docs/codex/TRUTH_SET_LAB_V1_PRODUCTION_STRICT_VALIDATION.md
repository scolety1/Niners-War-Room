# Truth Set Lab v1 Production Strict Validation

Status: rejected. This phase prepares the app to accept a corrected production export, but the current production files remain blocked.

## Files

- Strict validation summary: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\production_strict_validation_summary.csv`
- Strict validation flags: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\production_strict_validation_flags.csv`

## Strict Schema

The corrected production export must use this exact header:

```csv
player_name,position,nfl_team,season,games,games_started,passing_yards,passing_tds,interceptions,rushing_attempts,rushing_yards,rushing_tds,rushing_first_downs,targets,receptions,receiving_yards,receiving_tds,receiving_first_downs,total_touches,total_yards,total_tds,lve_points_estimate_if_calculable,source_name,source_url,source_date,confidence_0_100,notes
```

## Current Raw Export Result

- Status: `rejected`
- Header: `exact`
- Rows: 40
- Malformed-width rows: 30
- Numeric-error rows: 22
- Uncertain-marker rows: 7
- Embedded-url rows: 30
- Source-separation rows: 35
- Blocking flags: 168

## Current Clean/Rejection Metadata Result

- Status: `rejected`
- Header: `mismatch`
- Rows: 40
- Blocking flags: 321

## Validation Rules

- Exact header only.
- One row per truth-set player.
- Every row must have the same column count as the header.
- Numeric fields must be numeric or blank.
- Question marks are not allowed in numeric fields.
- URLs are not allowed in numeric/stat fields.
- `source_name` must not contain URLs.
- `source_url` must contain the URL when a URL is provided.

## Guardrail

This validator does not import production data into model scoring. It only decides whether a future corrected export is structurally safe enough for a preview import.
