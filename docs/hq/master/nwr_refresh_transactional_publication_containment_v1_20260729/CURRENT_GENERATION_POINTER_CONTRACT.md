# Current Generation Pointer Contract

`current_generation.json` is the sole authoritative commit point. Its schema
is `nwr-dynastyprocess-current-generation-pointer-v1` and it records:

- a safe generation ID;
- `generation_manifest.json`;
- the manifest SHA-256;
- publication state `PUBLISHED`;
- publication timestamp.

The pointer is built in a unique temporary regular file under the authenticated
safe root, flushed, identified by handle, and replaced once through an atomic
same-volume handle-bound rename.

Before replacement, the prior pointer selects the prior complete generation.
After replacement, the new pointer selects the new complete generation. No
individual CSV is a commit boundary and no mutable `latest` CSV set exists.

Missing, malformed, aliased, reparse-backed, wrong-schema, non-published, or
hash-inconsistent pointers fail closed. A pointer to an incomplete, malformed,
or mismatched generation also fails closed.
