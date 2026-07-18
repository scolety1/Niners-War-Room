# Validate Before Mutate Review

The writer projects untrusted refresh input into the closed schema, validates the provisional document, adds and verifies integrity, serializes the real candidate, and enforces the 2 MiB byte limit before validating any existing receipt path or taking any mutation snapshot. It repeats finalization immediately before staging.

Only after both candidate preflights succeed may the service snapshot latest, backup, archive, quarantine, and staging targets. The candidate is staged and atomically replaced. An interrupted or failed replace restores all captured snapshots and removes temporary artifacts. Rejected candidates therefore cannot create directories, rotate backup, archive or quarantine files, prune retention, stage bytes, replace latest, or otherwise change the receipt tree.

Tests compare complete directory-tree snapshots for unknown fields, invalid types and enums, privacy violations, oversized candidates including 2,102,591 bytes, and injected replace failures. Exact-limit acceptance and one-byte-over rejection are based on the actual serialized candidate bytes.
