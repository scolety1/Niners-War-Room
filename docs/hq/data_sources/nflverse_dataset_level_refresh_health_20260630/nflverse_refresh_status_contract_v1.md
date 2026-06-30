# NFLVerse Refresh Status Contract V1

Each nflverse dataset row reports independent axes:

- `execution_status`: `succeeded`, `failed`, `blocked_policy`, `blocked_config`, or `skipped`
- `freshness_status`: `fresh`, `stale`, `review`, `unknown`, or `not_applicable`
- `schema_status`: `pass`, `review`, `fail`, `unknown`, or `not_applicable`
- `coverage_status`: `pass`, `review`, `fail`, `unknown`, or `not_applicable`
- `row_count_status`: `pass`, `review`, `fail`, `unknown`, or `not_applicable`
- `missingness_status`: `pass`, `review`, `fail`, `unknown`, or `not_applicable`
- `policy_status`: packet source-policy value
- `headline_status`: derived UI badge

Failure is dataset-local. One failed nflverse dataset does not hide other dataset rows.
Missing evidence is never converted to zero, false, healthy, clean, no-role, no-injury,
or no-usage.

`ff_rankings` is visible as `blocked_policy` and is never auto-refreshed.
