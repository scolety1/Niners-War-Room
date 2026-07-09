# HQ1 Use Gate Template

Use this template in future NWR source, metric, ranking, formula, replay, or research packets.

## Artifact Or Lane

- Lane name:
- Artifact path:
- Base HQ commit:
- Source receipt IDs:
- Related packets read:

## Allowed After This Lane

- [State exactly what future lanes may use.]
- [State whether use is research context, review-only, display-only, or production/model-use.]
- [State any allowed file paths or artifact consumers.]

## Review-Only

- [List review-only sources, fields, metrics, candidates, outputs, or evidence.]
- [State why each item remains review-only.]
- [State what future lane is required before deeper use.]

## Display-Only

- [List display-only sources or fields.]
- [State whether display is human context only.]
- [State that display-only does not mean formula input.]

## Blocked

- [List blocked sources, fields, joins, metrics, formulas, or output paths.]
- [State the exact reason: proprietary, no safe public source, identity-unsafe, leakage-unsafe, route-denominator unsafe, or not enough information.]
- [State what would unblock each item.]

## Model-Approved

- [If nothing is model-approved, say: No metric, source, feature, or model input is approved.]
- [If anything is model-approved in a future lane, cite the source-admission packet, receipt chain, validation packet, and human approval.]

## Source-Truth Approved

- [If nothing is source-truth approved, say: No source-truth field or registry status is approved or changed.]
- [If anything is approved in a future lane, cite the source-truth admission artifact.]

## Promotion Requirements

Before promotion, a future lane must provide:

- source receipt chain
- licensing/use proof
- identity join audit
- missingness and coverage audit
- leakage safety check
- rebuild/replay checklist
- validation results from a separate lane
- explicit human or Master HQ approval

## Non-Changes

This lane does not change:

- production model
- rankings
- app/UI
- runtime behavior
- source truth
- default sort
- hidden sort
- recommendations, verdicts, boosts, trade logic, draft logic, or decision logic
