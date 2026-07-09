# High-Value Signal Next Data Upgrade Recommendation

## Recommended Next Lane

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

## Why This Lane

- It is the most executable missing feature branch found by the locator.
- It tests a narrow RB-only review hypothesis already preserved by Master HQ.
- It may add non-duplicate context beyond PYF/multi-year production/age/role.
- It does not require broad PFR promotion.
- It keeps PFF Elusive Rating and `nwr_elusive_proxy_review_only` blocked.

## Required Guardrails

- RB only.
- Review-only only.
- No production/model-use.
- No rankings integration.
- No broad PFR feature promotion.
- Compare against PYF, multi-year production, role, and rushing volume.
- Stop if source hashes, schema, identity joins, or as-of status cannot be validated.
