# Selected Candidate Formula Spec - Review Only

Baseline comparator:

- `baseline_v3_prior_points = prior_nwr_points`

Original candidate:

- `usage_opportunity_volume = 0.70 * prior_nwr_points + 0.30 * usage_proxy`
- `usage_proxy = 0.40 * prior_carries + 0.55 * prior_receptions + 0.20 * prior_targets + 0.15 * prior_opportunities`

Prior rescue carried forward:

- `qb_guard_soft_blend`: for QB rows with `prior_nwr_points >= 250` and `prior_games >= 12`, use `0.75 * baseline + 0.25 * original`; otherwise use original.

Prior refinement carried forward:

- `rb_wr_cutline_safe_blend`: RB/WR rows use `0.50 * baseline + 0.50 * qb_guard`; QB/TE rows retain `qb_guard_soft_blend`.

Selected redesign:

- `wr_boundary_breakout_sensitivity_guard`
- Start from `rb_wr_cutline_safe_blend`.
- For WR-only WR24/WR36 boundary drops, use `0.80 * baseline + 0.20 * qb_guard_soft_blend`.
- Boundary rule: baseline rank within 8 ranks inside WR24/WR36, current-best rank within 8 ranks outside, and prior targets/receptions/opportunities rank <= 60.

Allowed inputs:

- Feature-season factual fields from V3/source contract.
- Baseline and candidate prediction outputs.
- Position and predeclared cutline thresholds.

Blocked inputs:

- Target-season outcomes for guard assignment.
- Market, ADP, vendor, projection, or rank fields as source truth.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous `rz_att`, current-only roster/status/injury/depth/schedule context.

This spec is not a runtime config and is not production-approved.
