# Crash and Recovery State Machine

| State | Durable authority | Required recovery behavior |
|---|---|---|
| `STAGING` | old pointer | Ignore or later remove incomplete staging |
| `STAGED_COMPLETE` | old pointer | Complete manifest exists but is not current |
| `GENERATION_IMMUTABLE` | old pointer | Retain orphan generation or clean later |
| `COMMITTING_POINTER` | old pointer until rename | Retry with a new generation |
| `PUBLISHED` | new pointer | New complete generation remains current |
| `CLEANUP_PENDING` | new pointer | Retry non-authoritative cleanup |
| `FAILED_UNPUBLISHED` | old pointer | Preserve old complete generation |

Crash during any payload/manifest write, after immutable rename, or during
pointer temporary-file creation leaves the old pointer authoritative. Pointer
replacement failure also leaves the old pointer authoritative.

A simulated crash immediately after successful pointer replacement raises a
distinct committed-publication error; readback resolves the complete new
generation. Old-generation and stale-staging cleanup failures return
`CLEANUP_PENDING` without invalidating publication.

Startup readers inspect only `current_generation.json`. Maintenance inspection
may identify orphan immutable generations and stale staging IDs, but neither is
selected as current. Retry always creates a new unique generation and never
mutates an earlier one.
