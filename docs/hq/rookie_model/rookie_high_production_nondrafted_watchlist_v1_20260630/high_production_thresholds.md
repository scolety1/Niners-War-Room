# High-Production Thresholds

## Availability Decision

The watchlist cannot be populated safely yet.

CFBD production/context artifacts are present at:

- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_production_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/`

However, those artifacts are review-only and identity-review-required, and the historical CFBD candidate audit does not provide an approved historical join to the 2,514 likely non-drafted candidates.

Observed source posture:

- CFBD production rows inspected: 16938
- CFBD production rows marked review-only: 16938
- CFBD production rows requiring identity review: 16938
- CFBD production rows marked model-use allowed: 0
- CFBD production rows marked training allowed: 0
- historical CFBD approved candidate rows found: 0

## Future Threshold Rules Once Approved Joins Exist

Do not invent production values. Do not treat missing production as zero. Apply thresholds only to approved, identity-resolved college production/context rows.

### QB

- Top 5 percent within position/class by approved passing production composite, or
- Top 10 percent in at least two approved passing/context indicators such as yards, touchdowns, efficiency, and attempt volume, with clean identity.

### RB

- Top 5 percent within position/class by approved rushing/receiving production composite, or
- Top 10 percent in at least two approved indicators such as rushing yards, scrimmage yards, touchdowns, receptions, or dominator/market-share context if available.

### WR

- Top 5 percent within position/class by approved receiving production composite, or
- Top 10 percent in at least two approved indicators such as receiving yards, receptions, touchdowns, market share, dominator, or efficiency if available.

### TE

- Top 5 percent within position/class by approved receiving production composite for tight ends, or
- Top 10 percent in at least two approved TE-specific production/context indicators.

## Required Blockers

A row cannot be surfaced if identity is ambiguous, same-name collision is unresolved, class-year is ambiguous, college/team timeline is unresolved, or CFBD production is review-only without an approved identity join.
