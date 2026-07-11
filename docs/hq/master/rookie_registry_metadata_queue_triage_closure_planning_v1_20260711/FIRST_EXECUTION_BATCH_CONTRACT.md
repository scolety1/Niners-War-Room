# First Execution Batch Contract

## Decision

No closure batch satisfies the exact-proof gate. The first lane is proof preparation only.

- Batch ID: `batch_836e8658fea7760a7278dd66`
- Queue rows: `2`
- Category: `ARTIFACT_SOURCE_LINK_MISSING`
- Evidence state: `SUPPORTING_EVIDENCE`
- Locality: `LIVE_HQ`
- Proof state: `PARTIAL_PROOF_ONLY`
- Closure rows authorized: `0`

The batch contains the two non-conflicting queued artifact-to-source rows with deferred protected exact-hash candidates. The third protected candidate is excluded because its artifact is `DUPLICATE_CONFLICTING`.

## Authorized proof-preparation work

A future lane may read the two canonical queue rows and their exact existing hash evidence; confirm that each packet source reference is not a canonical source endpoint; prepare an opaque endpoint-registration decision request; prepare a protected-scope authorization request at exact purpose; specify the exact artifact/source receipt or manifest relationship required; and produce a mechanical readiness checklist. It must write only a new proof-preparation packet unless separately authorized.

It may not register or promote a source, add an active mapping, populate an optional foreign key, activate a deferred candidate, make a source/use decision, copy protected content, resolve identity, add player/evidence rows, or close any queue row.

## Proof required before any later closure

Both rows require:

1. exact artifact ID;
2. registered canonical source ID at exact grain;
3. explicit protected-scope authorization at exact purpose;
4. durable receipt or manifest explicitly connecting the exact artifact and canonical source IDs;
5. canonical proof SHA-256;
6. `NO_AUTHORITY_CHANGE_METADATA_REFERENCE_ONLY` or equivalent zero-effect confirmation;
7. `NO_SOURCE_PROMOTION` and `NO_SOURCE_OR_USE_PERMISSION_CHANGE` confirmation;
8. rights/privacy and locality clearance;
9. successful endpoint, relationship, hash, duplicate, and conflict validation;
10. append-only closure event containing the exact queue ID and commit.

## Stop conditions

Stop if a canonical source endpoint is absent; protected-scope authorization is absent; the packet reference is treated as a source endpoint; proof requires inference, identity, restricted content, or a reversible locator; authority or permission would broaden; a conflict emerges; any deferred candidate would activate; or any protected/frozen/runtime/app/ranking/formula/source-registry/plugin-governance path would change without separate authorization.

## Reversibility

This proof-preparation lane should create documentation only. Before adoption, revert its local commit. After adoption, correct it with a new superseding packet; never rewrite the planning packet or a future closure event.
