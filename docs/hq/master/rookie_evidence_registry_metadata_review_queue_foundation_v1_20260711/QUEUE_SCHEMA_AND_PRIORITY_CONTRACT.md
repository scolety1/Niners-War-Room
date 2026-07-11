# Queue Schema and Priority Contract

Frozen before queue population at `2026-07-11T11:52:14.3860972-06:00` on Phase B commit `660b59d4068e87df6fa997a0a0513c0f0c326eb1`.

## Closed categories

- `ARTIFACT_AUTHORITY_LINK_MISSING`
- `ARTIFACT_SOURCE_LINK_MISSING`
- `ARTIFACT_DATASET_LINK_MISSING`
- `ARTIFACT_RECEIPT_LINK_MISSING`
- `DATASET_SOURCE_LINK_MISSING`
- `DATASET_RECEIPT_LINK_MISSING`
- `RECEIPT_SOURCE_LINK_MISSING`
- `EXPLICIT_SOURCE_USE_DECISION_MISSING`
- `CONFLICTING_EXPLICIT_METADATA_LINK`
- `LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW`
- `RESTRICTED_RIGHTS_REVIEW`
- `OFF_HQ_AUDIT_LOCATOR_REVIEW`
- `NOT_ENOUGH_INFORMATION`

Player identity, alias, UDFA, player value, ranking, formula, recommendation, and player-evidence review categories are prohibited.

## Required row fields

Every append-only row contains an opaque queue ID, category, subject endpoint type/ID, optional related endpoint type/ID, evidence-state classification, locality, source/use implication, reason, exact supporting metadata artifact, prohibited automatic resolution, permitted future review action, required closure proof, status, deterministic governance priority, created-at receipt, append-only history reference, and initially blank closure receipt.

Statuses are exactly `OPEN`, `BLOCKED`, `NOT_ENOUGH_INFORMATION`, `DEFERRED`, and `CLOSED_WITH_RECEIPT`. No generated row may begin closed.

## Frozen governance-only priority rules

1. `P0_INTEGRITY_BLOCKER`: `CONFLICTING_EXPLICIT_METADATA_LINK` only.
2. `P1_AUTHORITY_OR_RIGHTS_BLOCKER`: missing artifact/dataset/receipt authority or source links, missing exact source/use decisions, and restricted-rights review.
3. `P2_LINEAGE_GAP`: missing artifact/dataset receipt or dataset lineage links.
4. `P3_AUDIT_OR_NO_RECREATE_GAP`: local-only availability and off-HQ audit-locator review.
5. `P4_INFORMATIONAL`: `NOT_ENOUGH_INFORMATION` category only when no stronger governance rule applies.

Priority never uses player identity, player quality, draft round, ranking impact, favorable data, fantasy relevance, or analyst preference.

## Deterministic status rules

- Integrity, authority, source, rights, and exact-decision blockers begin `BLOCKED`.
- Lineage gaps and local availability begin `NOT_ENOUGH_INFORMATION`.
- Off-HQ audit items begin `DEFERRED`.
- Pure informational items begin `OPEN`.
- `CLOSED_WITH_RECEIPT` is forbidden at generation time.

No queue row changes authority, source admission, permission, identity, evidence, or product behavior. Closure always requires a new exact receipt and append-only event; a loader or queue consumer may never close, merge, select, or resolve an item automatically.
