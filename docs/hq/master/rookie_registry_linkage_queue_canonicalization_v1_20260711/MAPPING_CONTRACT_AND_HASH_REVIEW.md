# Mapping Contract and Hash Review

- Canonical Git-blob SHA-256: `19bb737de35f476ad39bff50d41f25e5ec6ef3b88dacd48d23b47917960fa264` — PASS.
- Frozen timestamp recorded by the contract: `2026-07-11T02:21:53.5735740-06:00`.
- Source-worktree contract creation/last-write preceded mapping output; its last-write did not change after output inspection.
- The Phase B builder verifies the frozen contract hash before reading discovery inputs or writing mapping output.
- Accepted evidence types remain exactly the four frozen values: `VERIFIED_EXPLICIT_ID_REFERENCE`, `VERIFIED_EXACT_MANIFEST_REFERENCE`, `VERIFIED_EXACT_HASH_RECEIPT`, and `VERIFIED_EXPLICIT_DECISION_REFERENCE`.
- All 113 active links use `VERIFIED_EXACT_MANIFEST_REFERENCE`. The 25 external dataset/source candidates use explicit ID references and the 3 protected artifact/source candidates use exact hash receipts; all 28 remain deferred.
- Filename, proximity, title, semantic similarity, names or normalized names, row count, season, source-family defaults, local cache presence, public availability, narrative inference, and model judgment remain rejected proof.

The committed blob hash is authoritative. The isolated Windows checkout was temporarily restored to committed LF bytes for raw byte validation because system Git defaults to CRLF smudging; this changed no Git blob or source commit.
