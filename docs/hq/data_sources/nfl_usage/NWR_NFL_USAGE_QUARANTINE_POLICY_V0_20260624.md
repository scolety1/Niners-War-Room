# NFL Usage Quarantine Policy V0

Quarantine any source, field, artifact, or refresh when one of these conditions appears:

- schema mismatch
- missing required fields
- blocked fields present
- row count collapse
- duplicate explosion
- null spike
- stale data
- license/attribution missing
- source unavailable
- raw data attempted to be committed
- unsupported route truth claim
- app/model permission violation

Quarantined data remains review-only and cannot be promoted, app-wired, model-wired, ranked, sorted, or merged into source-truth files.
