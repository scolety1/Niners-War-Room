# NWR MASTER CODEX REQUEST — Decision Trust Strip and Evidence Consistency V1

## Objective
Implement one bounded, reversible, display-only trust strip across Dynasty Rankings, Player Compare, and Trading Lab by reusing existing admitted metadata and explanation/receipt services. Present the same compact vocabulary and order for source/evidence status, as-of/freshness, identity/join status, missingness, material caveats, and an expandable path to existing receipts. Unknown, stale, gated, and unavailable must remain distinct.

## Hard boundaries
- Do not change scores, ranks, formulas, sorting, recommendations, filters, eligibility, or hidden logic.
- Do not edit/regenerate frozen 2026 artifacts or promote/fetch/infer/substitute sources.
- Do not create a new explainer, health engine, manual queue, or movement engine.
- Do not use PYF, GAUNTLET_081, or current-board freeze as decision logic.
- Preserve Trading Lab as manual; no calculator, fairness verdict, or offer generator.

## Required first step
Create a field-level reuse map for existing explanation, receipt, identity, availability, source-governance, and data-health services. Stop if facts cannot be represented consistently without changing meaning/status.

## Acceptance
1. Documented schema and glossary. 2. Identical semantics across three surfaces with progressive disclosure. 3. Deterministic empty/unknown/stale/gated/identity-exception states. 4. Contract and surface tests. 5. Proof rank/formula/source/freeze paths unchanged. 6. Accessible labels and keyboard disclosure. 7. Representative fixtures/screenshots. 8. Local commit only; do not push absent later HQ authorization.

## Verdicts
- GREEN_DECISION_TRUST_STRIP_V1_READY_FOR_HQ_REVIEW
- YELLOW_DECISION_TRUST_STRIP_V1_COMPLETE_WITH_REVIEW_CAVEATS
- BLOCKED_DECISION_TRUST_STRIP_V1_SEMANTIC_OR_SOURCE_CONFLICT

Report verdict, files, surfaces, tests, protected/frozen results, branch, local commit and push status.
