# State Semantic Consistency Review

Result: PASS. The adapter, both surfaces, source glossary, fixture matrix, and focused tests use one canonical mapping and label set.

| State | Canonical label | Preserved meaning |
|---|---|---|
| `REFRESH_SUCCESS` | Refresh succeeded | Explicit approved refresh success only |
| `PARTIAL_SUCCESS` | Partial success | At least one succeeded portion and at least one incomplete portion |
| `STALE_RETAINED_DATA` | Stale retained data | Existing policy explicitly reports retained older data as stale |
| `SOURCE_SKIPPED` | Source skipped | Intentional recorded workflow skip, not failure |
| `SOURCE_UNAVAILABLE` | Source unavailable | Configuration or availability prevents access, not a policy gate |
| `SOURCE_GATED` | Source gated | Existing policy blocks admission, not unavailability |
| `REFRESH_FAILED` | Refresh failed | Explicit failed attempt with existing reason/diagnostic retained when supplied |
| `NOT_ENOUGH_INFORMATION` | Not enough information | Evidence cannot support a more favorable classification |

`FIELD_ORDER` fixes deterministic output order. Partial summaries expose succeeded and incomplete counts. Missing timestamps display `Not recorded`; missing reasons display an explicitly untrusted fallback rather than favorable state. Both page integrations call the same adapter and therefore cannot assign divergent labels.
