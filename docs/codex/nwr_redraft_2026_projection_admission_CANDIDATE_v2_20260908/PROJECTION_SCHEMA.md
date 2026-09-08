# Projection schema

The mechanical schema is in `PROJECTION_SCHEMA.csv`. `source_as_of` is not present in the
service's seven-column header tuple, but every row without a fresh ISO date is blocked, so it is
operationally required. Attempts, completions, carries, and targets can be retained as provenance
but Redraft V1 does not score them. K/DST require `projected_points_override`.

The service still requires a separate SHA-bound approval receipt before installation. This task did
not weaken that contract.
