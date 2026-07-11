# Queue Closure Pause and Reentry Gate

## Controlling pause

`ROOKIE_REGISTRY_METADATA_QUEUE_CLOSURE_PAUSED_PENDING_EXACT_CANONICAL_SOURCE_ENDPOINT_EVIDENCE`

The pause applies to batch `836e8658fea7760a7278dd66`, queue rows `queue_88b3986f5da27f5d0c585b6b` and `queue_d7111a1782f7cdba7c75f78a`, and any equivalent batch requiring the same missing canonical endpoint proof.

This pause is not queue closure, permanent rejection, source blocking beyond existing governance, source admission, an authority decision, or a source/use decision. Both rows remain open, blocked, unchanged, and closure-ineligible.

## Reentry trigger

Queue-proof review may reopen only after canonical HQ contains all of the following at exact grain:

1. Exact opaque source endpoint ID.
2. Exact source-family identity.
3. Explicit canonical relationship between source endpoint ID and source family.
4. Endpoint-grain rights status.
5. Endpoint-grain privacy class.
6. Exact artifact-to-endpoint relationship.
7. Evidence hash or receipt.
8. Explicit zero authority effect and zero use-permission effect.

A new review must cite the canonical append-only metadata trigger. External research or provider contact requires a separately authorized lane and is not a reentry trigger by itself.
