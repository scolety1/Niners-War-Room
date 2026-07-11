# Rookie Evidence Workspace V1

This directory is a metadata-first, read-only registry scaffold. It indexes the canonical design inventory without copying player observations, resolving identities, promoting sources, or authorizing ranking, formula, training, production-scoring, application, or product use.

`AUTHORITY_REGISTRY.csv` is copied only from the normalized 23-row authority contract. The legacy `canonical_now` field is retained as an opaque historical string and is never interpreted. Empty source, dataset, receipt, player, alias, identity-assertion, evidence-observation, and source/use decision registries fail closed until exact receipt-backed mappings exist.

Application runtime must not import this workspace or its loader. The companion service is read-only and intended only for tests and CLI diagnostics.
