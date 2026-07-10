# Miss-Specific Overlay Blocked Signal Policy

The following signals are blocked for overlay scoring:

- current-only ADP
- market/ADP without historical/as-of proof
- same-season or future context
- current/future injury status
- current/future team context
- CFBD/prospect production unless source/use and identity gates explicitly pass
- inferred UDFA truth without source evidence
- SportsDataIO
- paid API / free-trial / API-key sources
- PFF Elusive Rating
- `nwr_elusive_proxy_review_only`
- broad source promotion
- hidden sort or recommendation logic

Allowed review-only signals must remain lagged, source-gated, and explicitly non-production.
