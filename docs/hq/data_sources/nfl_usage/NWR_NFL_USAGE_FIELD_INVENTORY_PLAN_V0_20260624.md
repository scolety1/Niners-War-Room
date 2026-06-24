# NFL Usage Field Inventory Plan V0

## Goal

Run exact field introspection without committing raw data.

## Procedure

1. Use the project environment or an explicitly approved scratch environment with `nflreadpy`.
2. Set raw cache to `C:\NWR_SHARED_DATA\nfl_usage_cache\`.
3. Pull the smallest safe sample for each source family.
4. Immediately convert source frames to field lists, row counts, dtype summaries, min/max season/week coverage, and schema fingerprints.
5. Write raw files only to shared cache.
6. Commit only sanitized summaries under `docs/hq/data_sources/nfl_usage/review_artifacts/`.

## Required Checks

- Blocklisted fields are quarantined.
- License and attribution metadata are present.
- Route-related fields are proxy-labeled unless exact route-run truth is verified.
- All review rows retain `model_input_allowed=no` and `app_wiring_allowed=no`.
- Raw data paths are not tracked by Git.
