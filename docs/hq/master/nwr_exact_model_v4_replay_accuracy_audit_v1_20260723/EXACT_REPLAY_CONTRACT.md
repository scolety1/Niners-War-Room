# Exact replay contract

## Primary target

`EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY` applies the exact current production
Model v4 formula to inputs that were available at each historical decision date.
It is the required contract for evaluating the accuracy of the current model.

## Contract A — current-formula historical replay

- Formula authority: `docs/hq/model/model_v4_formula_documentation_cleanup_v1_20260708/MODEL_V4_ACTIVE_FORMULA_CONTRACT.md` and
  `docs/hq/model/model_v4_formula_documentation_cleanup_v1_20260708/MODEL_V4_COMPONENT_REGISTRY.csv`.
- Formula identity: `model_v4_wr_qb_v2_old_pocket_qb_guardrail` on the accepted
  scored board; documented fallback is not interchangeable.
- Required sequence: admitted as-of components -> position-specific score ->
  lifecycle modifier -> confidence cap -> discipline/safety layers ->
  `checkpoint_review_score` -> exact Model v4 score -> deterministic rank.
- Position logic: the registry's RB/WR/QB/TE component formulas and weights.
- Confidence and lifecycle: exact historical inputs and outputs are required;
  the review-only sidecars are not silently promoted.
- Rank/ties: score descending, exact governed stable secondary ordering. The
  production proxy's name tie-break is not authority for the missing exact rank
  receipt.
- Missing data: a row is excluded from the exact subset if any required
  component is not exact original or exact deterministic regeneration.
- Sources: only tracked/admitted sources available before target-season outcome.
- Availability: zero complete historical rows; contract is blocked by receipts.

## Contract B — historical-version replay

Apply the exact model version active at each checkpoint, including that version's
components, lifecycle, confidence, safety, missingness, and tie rules. Versioned
checkpoint manifests were not recovered, so this contract is also blocked. It is
useful for deployment-history analysis, not the primary current-model question.

## Contract C — accepted production-proxy replay

The accepted proxy reuses historically lagged production fields, position weights,
documented missing-component penalties, and deterministic ranking. It has 5,518
rows for 2013-2025. It is leakage-safe and reproducible, but it is a
`PARTIAL_REPLAY`: it is not an exact score/checkpoint/rank replay and may not fill
the exact subset.

The three contracts remain separate throughout this packet.
