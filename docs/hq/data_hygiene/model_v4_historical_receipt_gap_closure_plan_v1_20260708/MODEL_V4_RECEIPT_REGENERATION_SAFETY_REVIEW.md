# Model v4 Receipt Regeneration Safety Review

## Current Status

Regeneration is not approved by this packet.

Some missing receipts may be regeneratable for review-only evidence, but only after Master HQ approves a bounded regeneration contract. Regeneration must never tune weights, optimize formulas, run Formula Gauntlet, select winners, promote sources, write canonical `local_exports`, or alter app/ranking behavior.

## Safe Regeneration Preconditions

Before any regeneration lane:

1. Define feature season and target season.
2. Freeze source inputs and hashes.
3. Prove source admission/use gate for every input.
4. Prove identity joins with canonical IDs and no name-only approval.
5. Prove missingness semantics and no missing-as-zero shortcuts.
6. Prove the transform/config existed by the feature-season decision date or label it as a challenger/proxy, not exact Model v4.
7. Write outputs only to scoped docs/review artifact paths or approved local-only review output paths.

## Regeneration Safety By Gap

- `checkpoint_review_score`: review-only regeneration is unsafe until exact historical transform/config and input receipts are known. Recovery is preferred.
- `position_specific_review_score`: review-only regeneration is possible only if component transform receipts and weights are frozen by feature season.
- lifecycle/age: may be safely regenerated from birth date and feature-season date if identity and source receipt are safe.
- role archetype: may be regenerated only from lagged factual usage/roster context with explicit source gates.
- confidence caps: may be regenerated only from feature-season missingness and coverage receipts.
- WR/QB v2 overlay: requires human review because it affects candidate decision logic.
- routes/YPRR/TPRR: blocked until Route Recovery admits a rights-cleared denominator source.
- red-zone: possible as review-only once semantics and coverage are admitted.
- shadow metrics: blocked until source file or exact generating contract is found.

## Leakage Controls

Regeneration must exclude:

- target-season outcomes as features
- current roster/status/injury/depth/schedule context backfilled into history
- current market, ADP, projections, rankings, or vendor context
- labels used as inputs
- candidate overlay decisions inferred from current board only

## Conclusion

Recovery from existing artifacts is safer than regeneration for exact Model v4 replay. Regeneration can support review-only challenger or proxy analysis only if Master HQ explicitly approves the scope and the output remains non-production.
