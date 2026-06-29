# Gate F Display Artifact Spec - 2026-06-30

## Rules

- review-only and display-only
- not Rankings-wired in this lane
- no hidden sort logic
- missing data is `Not enough information`, never `0%`
- only Gate D allowed features are used
- Gate E review-only validation must exist before rates are displayed
- market, ADP, DynastyProcess, vendor, Gmail, projections, and CFBD production are not used

## Status Fields

- identity_status
- draft_capital_status
- feature_coverage_status
- model_rd_status
- validation_status
- display_status
- data_quality_status
- review_only=true
- display_only=true
- model_use_allowed=false
- training_allowed=false
- rankings_wiring_allowed=false
