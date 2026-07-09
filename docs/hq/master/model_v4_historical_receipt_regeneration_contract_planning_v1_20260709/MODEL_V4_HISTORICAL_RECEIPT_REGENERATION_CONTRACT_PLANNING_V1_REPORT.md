# Model v4 Historical Receipt Regeneration Contract Planning V1

## Verdict

`YELLOW_HISTORICAL_RECEIPT_REGENERATION_CONTRACT_READY_WITH_CAVEATS`

## Clear Answer

The regeneration contract is ready as a review-only planning artifact, but future regeneration should start with only `confidence_cap_receipts` after explicit Master HQ approval. This lane did not regenerate receipts.

## Contract Scope

Included receipt families:

- `confidence_cap_receipts`
- `role_archetype_receipts`
- `red_zone_exact_receipts`

Explicitly excluded:

- `route_yprr_tprr_exact_receipts`
- `shadow_model_v2_metrics`
- `return_scoring_receipts`

## Future Regeneration Safety Decision

Future regeneration is not approved by this packet. The safest next executable lane is a one-family pilot for `confidence_cap_receipts`, because it can be framed as coverage, missingness, and use-gate context using source-traced existing artifacts. `role_archetype_receipts` should wait for the confidence pilot. `red_zone_exact_receipts` should wait until exact source artifacts and as-of safety are proven.

## Why This Contract Is Cautious

The prior Master HQ review admitted no partial replay support and did not clear exact Model v4 replay. The freeze preserved useful current-board and partial/proxy evidence, but it did not provide exact season-by-season historical receipts. Therefore this packet defines future rules, stop conditions, output schemas, and evidence requirements only.

## Required Future Lane Behavior

A future regeneration lane must write only to review artifact paths, preserve review-only status, include hashes, row counts, schema validation, leakage checks, identity checks, missingness flags, and source/use-gate classifications. It must not write canonical `local_exports`, change model/ranking/app/runtime behavior, run replay, run Formula Gauntlet, tune weights, or claim production accuracy.

## Current Clearance

- Exact Model v4 replay: blocked.
- Formula Gauntlet tournaments: blocked.
- Production/model-use: blocked.
- Review-only component signal tests: still maximum clearance, requiring a separate execution contract.

## Recommendation

Next lane: `Model v4 Confidence Cap Receipt Regeneration Pilot V1`, planning-approved only after Master HQ explicitly authorizes execution.
