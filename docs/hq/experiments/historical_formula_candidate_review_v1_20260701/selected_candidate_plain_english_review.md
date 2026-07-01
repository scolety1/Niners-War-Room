# Selected Candidate Plain-English Review

`usage_opportunity_volume` keeps 70% of the frozen prior-season scoring baseline and replaces 30% with a simple usage proxy built from carries, receptions, targets, and opportunities.

What changed versus baseline:

- Players with stronger prior-season opportunity volume get nudged upward.
- Players whose prior points were less supported by usage get nudged downward.
- The formula does not use null-fenced snap, air-yard, or YAC fields.
- It does not use routes, TPRR, YPRR, red-zone sidecars, market data, projections, ranks, or current-only context.

The candidate improved validation and holdout MAE while keeping aggregate rank/order and startable precision stable. It is interpretable enough for human review, not for production promotion.
