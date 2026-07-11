# Deterministic Mapping Evidence Contract

Frozen before linkage discovery at `2026-07-11T02:21:53.5735740-06:00` against HQ base `7bc0523057562b75be6d2d6da890b58526aeaec5`.

## Permitted proof types

- `VERIFIED_EXPLICIT_ID_REFERENCE`: an existing canonical artifact or receipt explicitly names both endpoint IDs at the required grain.
- `VERIFIED_EXACT_MANIFEST_REFERENCE`: a canonical manifest explicitly connects endpoints using exact IDs or an exact repository-relative path.
- `VERIFIED_EXACT_HASH_RECEIPT`: an exact hash and explicit receipt/manifest relationship prove the link without inference.
- `VERIFIED_EXPLICIT_DECISION_REFERENCE`: an existing decision explicitly names `dataset_id × field_family × purpose` and the exact decision value.

Every verified link must record a mapping ID, both endpoint types and IDs, one permitted proof status, exact evidence artifact and field, evidence hash when relevant, locality, authority effect, source/use effect, caveat, and review status. A link is metadata only and cannot change authority, admission, player truth, availability, or use permission.

## Closed mapping statuses

- `VERIFIED_EXPLICIT_ID_REFERENCE`
- `VERIFIED_EXACT_MANIFEST_REFERENCE`
- `VERIFIED_EXACT_HASH_RECEIPT`
- `VERIFIED_EXPLICIT_DECISION_REFERENCE`
- `UNRESOLVED_NO_EXPLICIT_LINK`
- `CONFLICTING_EXPLICIT_LINKS`
- `LOCAL_ONLY_METADATA_ONLY`
- `RESTRICTED_SANITIZED_ONLY`
- `OFF_HQ_AUDIT_ONLY`
- `NOT_APPLICABLE`

## Permitted relationship targets

Only artifact→authority, artifact→source, artifact→dataset, artifact→receipt, dataset→source, dataset→receipt, receipt→source, and exact dataset/field-family/purpose decisions may be assessed.

## Rejected proof

Filename similarity, path proximity, directory membership alone, title or semantic similarity, normalized names, player names, source-family assumptions, broad policy defaults, timestamps, row counts, season overlap, favorable content, local cache presence, public accessibility, narrative implication, and model judgment are never proof. Names cannot control identity or metadata joins. Missing exact proof remains absent from active foreign-key fields.

## Fail-closed rules

Unresolved and conflicting mappings are review metadata only. Local-only, restricted, and off-HQ locators cannot create active evidence links. A broad receipt, policy, or family statement cannot become an exact decision. One purpose never expands to another. Review use never becomes model-training or production-scoring permission. Player, alias, identity, evidence-observation, player-value, draft-status, and UDFA links are prohibited.
