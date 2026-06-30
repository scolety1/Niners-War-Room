# Outcome V2 2000-2024 Validation/Calibration Gate - Input Coverage And Source Policy

## Source Inputs

This gate reuses the review-only 2000-2024 exact-scoring Outcome V2 historical
labels produced by the prior coverage probe:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe\outcome_v2_extended_season_outcome_labels.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe\outcome_v2_extended_anchor_horizon_labels.csv`

The raw/cache source audit remains outside git:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_source_audit_2000_probe\`

## Source Policy Status

Policy result: `PUBLIC_NFLREADPY_ALLOWED_REVIEW_ONLY`

The prior source probe found `GREEN_2000_EXACT_COVERAGE_AVAILABLE`:

- Seasons `2000-2011` loaded successfully through
  `nflreadpy.load_player_stats(summary_level="reg")`.
- Required scoring fields are present.
- Required first-down fields are present and non-null:
  `passing_first_downs`, `rushing_first_downs`, `receiving_first_downs`.
- No first-down approximation was used.
- Missing first-down fields were not treated as zero.

## Scoring Mode Confirmation

All 13,652 2000-2024 season label rows use:

`exact_verified_first_downs`

The generated labels retain guardrail flags:

- `model_input_allowed=no`
- `training_allowed=no`
- `app_wiring_allowed=no`

## Coverage Counts

| Metric | Value |
| --- | ---: |
| Season label rows | 13,652 |
| Anchor horizon rows | 13,652 |
| Complete this-year rows | 9,731 |
| Complete next-year rows | 7,566 |
| Complete within-5Y rows | 2,701 |
| Censored/missing within-5Y rows | 10,951 |

## Complete 5Y Rows By Position

| Position | Complete 5Y rows |
| --- | ---: |
| QB | 501 |
| RB | 586 |
| WR | 1,016 |
| TE | 598 |

## Review-Only Boundary

Allowed in this gate:

- Historical label validation/calibration.
- Field-level review-only approval/block decisions.
- Documentation and sanitized decision table.

Not allowed in this gate:

- Current-player probability activation.
- Rankings or Outcome Lens wiring.
- Model input promotion.
- Source-truth promotion.
- Protected artifact mutation.
- latest_candidate/latest_approved updates.
- Broad refresh, vendor scraping, Gmail scraping, or model_v4 rebuilding.

Generated shared-data validation artifacts are not tracked.
