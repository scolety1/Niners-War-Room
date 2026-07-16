# LocalData Pack Contract

- Pack ID: `nwr-local-data-receipt-pack`
- Version: `1.0.0`
- Schema: `1`
- Sole allowed root: repository-local ignored `local_exports/`
- Manifest: `local_exports/LOCAL_TEST_PACK_MANIFEST.json`
- Required rights attestations: `ownerAuthorized`, `noRedistribution`, and `noCheckIn` are true.
- Collection: exactly the 89 tracked test files listed by `tests/hermetic_localdata_manifest.json`.

Private Sleeper/LVE data, licensed Rotowire exports, rights-unresolved provider data, real histories, private plugin output, credentials, and real account/league identifiers remain outside tracked fixtures. The gate never searches elsewhere, copies the pack, or falls back to arbitrary disk files.

When the manifest is absent, collection does not begin. Output is exactly `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit `4`; it is not a pass, skip, xfail, or Hermetic result.
