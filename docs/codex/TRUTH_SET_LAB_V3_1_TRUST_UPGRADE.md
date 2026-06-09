# Truth Set Lab v3.1 Trust Upgrade

Status: review-only. This phase adds caution and preview reports only.

## What Changed

- Built a preview-only first-down projection estimator from v3 historical nflverse first-down rates.
- Added a WR/TE route-proxy caution worklist so route gaps are not hidden.
- Added a current injury review template for sourced notes only.
- Did not change model scores, formulas, active rankings, or readiness gates.

## Summary

- First-down projection rows: 40
- Estimated from history rows: 37
- Missing first-down projection rows: 3
- Route-proxy caution rows: 27
- Injury review rows: 33

## Files

- First-down estimates: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_first_down_projection_estimates.csv`
- First-down rates: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_first_down_projection_rates.csv`
- First-down summary: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_first_down_projection_summary.csv`
- Route-proxy cautions: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_route_proxy_caution_worklist.csv`
- Injury review template: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_injury_review_template.csv`
- Summary CSV: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_trust_upgrade_summary.csv`
- Summary JSON: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_trust_upgrade_summary.json`

## Use

Use these reports to inspect uncertainty while the agents finish source discovery. The estimates are not active scoring and should not unlock decision-ready status by themselves.
