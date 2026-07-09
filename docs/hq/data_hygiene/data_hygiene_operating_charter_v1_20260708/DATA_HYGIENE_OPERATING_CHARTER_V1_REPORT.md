# Data Hygiene Operating Charter V1

Verdict: `GREEN_DATA_HYGIENE_CHARTER_READY`

Canonical HQ base verified before work: `b25157c1dfe065f4d1f181c8e26a32fddce5cd66`

This packet defines the NWR Data Hygiene / Data Audit lane boundary. It is docs-only. It approves no source, model, formula, ranking, app behavior, production use, hidden sort, recommendation, canonical merge, or remote push.

## Governing Standard

Data Hygiene uses HQ1's receipt-chain/use-gate standard:

`docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708/`

Every Data Hygiene review must answer:

1. Do we actually have the information?
2. Where did it come from?
3. Is it reliable enough for the intended use?
4. Is it production/model-use, review-only, display-only, blocked, identity-unsafe, leakage-unsafe, or not enough information?
5. Can it be reproduced?
6. Can it be tested historically without leakage?

## What Data Hygiene Owns

Data Hygiene owns the evidence layer:

- source inventory
- source admission status
- receipt chains, source receipts, component receipts, and rebuild receipts
- board/input manifests
- hash checks and reproducibility evidence
- provenance maps
- join safety, player identity joins, duplicate rows, missing IDs, name conflicts, and join collisions
- season/week alignment
- current vs historical join safety
- coverage and missingness, including row counts, season coverage, position coverage, field coverage, missingness flags, and sparse-history flags
- leakage checks, decision-date safety, future-known fields, current-only fields used historically, post-outcome data leakage, and historical replay eligibility
- rebuildability, including input presence, script presence, hash reproducibility, local_exports dependency, and missing-file blockers
- data readiness gates for Formula Gauntlet, Route Recovery admission, historical replay, app display, and Master HQ promotion review

Data Hygiene may produce review packets, matrices, receipt chains, use-gate checklists, source-status recommendations, blocker reports, and handoff packets.

## What Data Hygiene Does Not Own

Data Hygiene does not own:

- source promotion
- production/model-use approval
- production ranking approval
- app/runtime behavior approval
- ranking changes
- formula tuning
- formula tournaments
- formula winner selection
- hidden sort logic
- recommendation logic
- model weight changes
- canonical merges
- remote pushes unless explicitly approved for a bounded docs-only action
- production activation
- production accuracy claims
- final Master HQ promotion decisions

## Operating Rule

Research first. Source trace first. Code second.

If evidence is incomplete, Data Hygiene should say `NOT_ENOUGH_INFORMATION`, `MISSING_SOURCE`, `MISSING_RECEIPT`, `REBUILD_BLOCKED`, `JOIN_BLOCKED`, `IDENTITY_UNSAFE`, or `LEAKAGE_UNSAFE`. It should not guess.

## Master HQ Boundary

Master HQ owns synthesis, lane routing, merge review, canonicalization, promotion decisions, production approval, formula/app/ranking decision authority, and cross-lane conflict resolution.

Data Hygiene hands off to Master HQ whenever evidence might become source promotion, model use, production ranking use, app behavior, formula input, canonical merge, or production claim.
