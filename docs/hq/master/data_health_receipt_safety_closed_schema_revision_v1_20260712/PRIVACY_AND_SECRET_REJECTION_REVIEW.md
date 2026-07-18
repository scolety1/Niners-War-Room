# Privacy and Secret Rejection Review

The persisted v2 document is constructed field by field. The orchestrator no longer passes
its full result mapping to the receipt store. Runner/cache/command/artifact paths, environment
variable names, provider detail, source rows, raw output, formulas, rankings,
recommendations, and arbitrary metadata are absent from the narrow input and persisted
allowlist.

Unknown top-level and result keys fail. Any input result value that is a mapping, list, tuple,
or set fails. Recursive document validation rejects unknown nested keys and unauthorized
types. Key and string privacy checks reject authorization/bearer material, API/access/refresh
tokens, cookies/session IDs, passwords, credentials, client secrets, raw headers, provider
payload/response labels, stack traces, and absolute Windows/UNC/POSIX paths.

The receipt does not sanitize then retain arbitrary text. `error_category` is mechanically
derived from closed operational state, and `error_summary` is selected from a fixed bounded
map. This prevents provider or diagnostic pass-through while preserving failure category.

Adversarial cases for nested authorization, nested bearer data, API-key-like keys,
cookie/session keys, both absolute path families, raw provider objects, and arbitrary nested
metadata all reject before mutation. A scan of changed implementation paths found no cloud
storage, database, provider call, credential literal, private-key block, or raw payload
persistence.
