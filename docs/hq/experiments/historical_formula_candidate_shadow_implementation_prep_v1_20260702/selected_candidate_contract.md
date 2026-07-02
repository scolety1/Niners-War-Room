# Selected Candidate Contract

Candidate: `wr_boundary_breakout_sensitivity_guard`

Status: `REVIEW_ONLY_SHADOW_IMPLEMENTATION_PREP`

Allowed action in this branch:

- Produce static documentation, schemas, comparison contracts, watchlist rules, and a safe implementation checklist.
- Preserve the selected candidate as human-review-only evidence.

Disallowed action:

- No production formula replacement.
- No app page, Streamlit page, live preview, rank sort, hidden sort, recommendation, model behavior, source-truth, runtime, or production config change.
- No candidate output may be wired into NWR.

Formula family carried forward:

- Role: `selected_fixed_targeted_redesign`
- Formula definition: `Start from current best; for WR24/WR36 boundary drops with usage breakout sensitivity, use 0.80 * baseline + 0.20 * qb_guard`
- Guard definition: `WR only, baseline within 8 ranks inside WR24/WR36, current best within 8 ranks outside, and prior targets/receptions/opportunities rank <= 60`
- Threshold policy: `WR cutlines = WR24/WR36; inside/outside band = 8; usage rank threshold = 60; all predeclared before evaluation`
- Allowed inputs: `feature-season position; prior_targets; prior_receptions; prior_opportunities; baseline/current-best predictions and ranks`

Approval fields:

- review only: `true`
- production approved: `false`
- shadow implementation approved: `false`
- static shadow implementation prep: `allowed for human review only`
