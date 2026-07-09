# Data Hygiene / Master HQ Interface

Master HQ owns synthesis, lane routing, merge review, canonicalization, promotion decisions, production approval, formula/app/ranking decision authority, and cross-lane conflict resolution.

Data Hygiene owns evidence readiness.

## Data Hygiene Sends To Master HQ

- verdict
- artifact path
- source/data reviewed
- what exists
- what is missing
- source status
- receipt status
- join safety
- leakage status
- reproducibility status
- coverage/missingness
- blockers
- allowed uses
- blocked uses
- recommendation
- whether a Master HQ decision is required

## Master HQ Decides

- whether a source is promoted
- whether a model/formula may use a field
- whether a board/ranking becomes production-active
- whether a benchmark/replay supports promotion
- whether app/runtime behavior changes
- how conflicting lanes are resolved
- whether review-only evidence becomes model-use
- whether canonical merge/canonicalization proceeds

## Interface Contract

Data Hygiene must be explicit and conservative. Master HQ should receive enough source trace to decide without guessing.

Data Hygiene should never bury caveats. If a source is useful but not reliable enough, say so.
