# Triage Classification Contract

## Scope

These classifications are derived planning metadata. They do not alter canonical queue status, priority, reason, authority, evidence state, source state, use permission, or closure receipt.

## Frozen planning statuses

- `POTENTIALLY_CLOSABLE_EXISTING_EXPLICIT_RECEIPT`
- `POTENTIALLY_CLOSABLE_EXISTING_EXACT_MANIFEST`
- `REQUIRES_NEW_AUTHORITY_DECISION`
- `REQUIRES_NEW_SOURCE_OR_DATASET_ENDPOINT`
- `REQUIRES_EXPLICIT_SOURCE_USE_DECISION`
- `REQUIRES_RIGHTS_OR_PRIVACY_DECISION`
- `LOCAL_ONLY_AVAILABILITY_BLOCKER`
- `RESTRICTED_LOCATOR_BLOCKER`
- `OFF_HQ_AUDIT_ONLY`
- `CONFLICTING_EVIDENCE_ESCALATION`
- `NOT_ENOUGH_INFORMATION`
- `NOT_APPLICABLE`

## Deterministic precedence

Apply the first matching rule:

1. `DUPLICATE_CONFLICTING` evidence state or a conflicting exact proof candidate → `CONFLICTING_EVIDENCE_ESCALATION`.
2. `LOCAL_ONLY_RESTRICTED` direct rights-review row → `REQUIRES_RIGHTS_OR_PRIVACY_DECISION`; its relationship rows → `RESTRICTED_LOCATOR_BLOCKER`.
3. `OFF_HQ_BRANCH_ONLY` → `OFF_HQ_AUDIT_ONLY`.
4. `LOCAL_ONLY` → `LOCAL_ONLY_AVAILABILITY_BLOCKER`.
5. A complete permitted explicit receipt at exact queue grain → `POTENTIALLY_CLOSABLE_EXISTING_EXPLICIT_RECEIPT`.
6. Otherwise, a complete permitted exact manifest at exact queue grain → `POTENTIALLY_CLOSABLE_EXISTING_EXACT_MANIFEST`.
7. `ARTIFACT_AUTHORITY_LINK_MISSING` → `REQUIRES_NEW_AUTHORITY_DECISION`.
8. `ARTIFACT_SOURCE_LINK_MISSING` or `ARTIFACT_DATASET_LINK_MISSING` → `REQUIRES_NEW_SOURCE_OR_DATASET_ENDPOINT`.
9. An explicit source/use-decision category, if ever present → `REQUIRES_EXPLICIT_SOURCE_USE_DECISION`.
10. `ARTIFACT_RECEIPT_LINK_MISSING` without complete proof → `NOT_ENOUGH_INFORMATION`; its action field must say canonical receipt endpoint and exact receipt relationship are required.
11. `NOT_APPLICABLE` requires an exact controlling decision naming the queue row or exact subject and relationship. Absence, supersession, duplication, or newer evidence is never enough.

Current counts are 23 conflict; 795 local-only; 12 restricted locator; 3 rights/privacy; 95 off-HQ; 970 new authority; 2,166 new source/dataset endpoint; 1,083 not enough information; and 0 for the other statuses.

## State-treatment rules

- `SUPERSEDED` retains category/locality routing. A successor does not prove the original relationship and does not make the row not applicable.
- `IDENTITY_UNRESOLVED` may proceed only with proof mechanically independent of names, aliases, normalized identity, or player joins. Stop if identity is required.
- `SOURCE_UNADMITTED` retains category routing only with `NO_SOURCE_OR_USE_PERMISSION`. Any admission or use authorization requires a separate exact decision.
- `DUPLICATE_EQUIVALENT` does not permit row collapse, preference, or inferred relationships.
- `DUPLICATE_CONFLICTING` always escalates.

## Proof-candidate states

Queued proof-state partitioning is strict:

- `EXACT_PROOF_PRESENT`: both canonical endpoints, permitted exact relationship, required hash/manifest, rights/locality result, and effect confirmations are complete.
- `PARTIAL_PROOF_ONLY`: an explicit documented relationship candidate exists but at least one required endpoint, authorization, or closure element is absent.
- `CONFLICTING_PROOF`: two or more explicit endpoint proofs disagree. Evidence-state conflict alone is not mislabeled as conflicting endpoint proof.
- `PROOF_NOT_FOUND`: no allowed explicit relationship candidate exists. A naked artifact hash is a prerequisite, not a relationship candidate.
- `PROOF_RESTRICTED_OR_LOCAL_ONLY`: proof or correspondence cannot activate because locality, availability, rights, or privacy remains unresolved.
- `PROOF_OFF_HQ_AUDIT_ONLY`: evidence is retained only for audit/no-recreate handling and requires an external trigger.

The queued partition is 0 exact, 3 partial, 0 conflicting explicit proof, 4,224 proof not found, 825 restricted/local-only, and 95 off-HQ.

## Batch key

Rows share a batch only when the following full key is identical: queue category; subject endpoint type; missing endpoint type; evidence-state class; locality class; rights/privacy class; primary planning status; proof-candidate state; candidate-scope class; exact required proof type; permitted future action; prohibited shortcuts; and closure gate.

`proof_pattern_id` is `proofpat_` plus the first 24 lowercase hexadecimal characters of SHA-256 over the UTF-8 pipe-joined key. `batch_id` is `batch_` plus the first 24 lowercase hexadecimal characters of SHA-256 over `batch|` plus that key. This produces 69 unique execution-safe groups. Every queue row belongs to exactly one group.

## Prohibited inference

Path, filename, directory, title, semantics, source family, normalized name, player name, season, row count, timestamp, public availability, local cache, favorable content, and model judgment are never proof. Planning status never authorizes a mapping, endpoint, decision, closure, identity resolution, source promotion, authority change, or use-permission change.
