# Engineering / QA / Security Synthesis

## Key engineering faults

1. Hard-coded Windows paths in production services.
2. Page-level `sys.path.insert` import hacks.
3. Untested service modules and missing service-test map.
4. Duplicative model/truth-set service families.
5. Hard-coded row counts and hashes in service code.
6. Git subprocess use in health dashboard.
7. Runtime draft state stored locally without strong backup/recovery.
8. UI and refresh controller logic coupled in Streamlit pages.
9. Fragmented secrets/API key setup.
10. Synchronous refresh execution blocks UI.

## Safe engineering work now

- Central path/settings module.
- Import/package cleanup.
- Service-test mapping.
- Runtime state backup/export/import/recovery.
- Refresh controller extraction.
- Secrets/settings masking and diagnostics.
- Local preflight script.

## Not safe yet

- Hosted deployment.
- Hosted DB state store.
- Async refresh queue that can pull blocked/manual sources.
- Service architecture consolidation that changes model/rank behavior.

## Must-fix before hosted/production

- No production hard-coded `C:\NWR...` paths.
- No raw/vendor/Gmail/secret files tracked.
- No protected artifact writes.
- Runtime state persistent/backed up/exportable/importable/recoverable.
- Refresh framework testable outside UI.
- Secrets masked and configurable.
- Preflight gate exists and passes.
