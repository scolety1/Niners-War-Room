# Season N To Season N+1 Policy

Season N feature candidates may be assembled only after season N factual stats are finalized. They may be used only to review season N+1 target outcomes in a future gated review dataset builder.

## Rules

- Feature season must be explicit.
- Target season must be strictly later than feature season.
- Full-season aggregates are illegal for same-season final targets.
- In-season or rolling windows require a separate point-in-time replay gate.
- Missing values remain `Not enough information` unless an observed source row or approved zero-eligibility denominator proves zero.
- Labels are evaluation targets, not input features.
- No ADP, market, DynastyProcess, projection, analyst rank, vendor opinion, current rank, or target label may appear as a feature.

This packet does not approve experiments. It only authorizes future construction of a review-only candidate dataset spec.
