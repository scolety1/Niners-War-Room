# Truth Set Lab v1 Role/Usage Strict Validation

Status: rejected. This phase prepares the app to accept a corrected role/usage export, but the current role/usage file remains blocked.

## Files

- Strict validation summary: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\role_usage_strict_validation_summary.csv`
- Strict validation flags: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\role_usage_strict_validation_flags.csv`

## Strict Schema

The corrected role/usage export must use this exact header:

```csv
player_name,position,nfl_team,season,snap_share,route_participation,routes_run,target_share,targets_per_route_run,yards_per_route_run,rb_carry_share,rb_target_share,weighted_opportunities,red_zone_touches,goal_line_touches,source_name,source_url,source_date,confidence_0_100,notes
```

## Current Export Result

- Status: `rejected`
- Header: `mismatch`
- Rows: 40
- Malformed-width rows: 40
- Numeric-error rows: 0
- Uncertain-marker rows: 26
- Prose numeric rows: 3
- Embedded-url rows: 0
- Source-separation rows: 0
- Blocking flags: 70

## Validation Rules

- Exact header only.
- One row per truth-set player.
- Numeric fields must be numeric, percent-formatted, or blank.
- Question marks are not allowed in numeric fields.
- RB workload prose is rejected as numeric evidence.
- URLs are not allowed in numeric/stat fields.
- `source_name` must not contain URLs.
- `source_url` must contain the URL when a URL is provided.

## Guardrail

This validator does not import role/usage data into model scoring. It only decides whether a future corrected export is structurally safe enough for preview import.
