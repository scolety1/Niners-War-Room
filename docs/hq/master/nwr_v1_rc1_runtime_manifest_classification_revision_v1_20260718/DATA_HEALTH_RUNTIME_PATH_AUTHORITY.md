# Data Health runtime path authority

## Purpose and caller

`is_runtime_state_path` supports the Data Health guardrail row `No runtime JSON tracked`. Its only production caller is `_guardrail_health`, reached from `build_data_health_dashboard`. The caller passes strings returned by `git ls-files`; therefore production inputs are repository-relative tracked paths, normally with Git/POSIX separators. The helper also accepts `pathlib.Path` and absolute service-owned runtime paths so the ownership contract can be tested directly.

## Normalization

The helper converts Windows separators to `/`, removes empty and `.` components, lexically resolves `..` components without allowing unresolved leading traversal to inherit a trusted prefix, and case-folds segments for the supported Windows environment. Root tests compare complete normalized segments from the beginning of the path. Directory names that merely contain `docs`, `hq`, `local_exports`, or a runtime-root name do not inherit authority.

## Tracked documentation authority

The canonical tracked evidence root is the exact segment prefix `docs/hq`. Within that root, generic metadata basenames `manifest.json`, `metadata.json`, and `receipt.json` are documentation metadata, independent of case and of words such as `runtime` in ancestor packet names. This is deliberately narrower than `if "docs" in path`: `docs-hq` is not trusted, and `docs/hq/evidence/draft_runtime_state.json` retains fail-closed runtime classification because its basename is runtime-specific.

The required path `docs/hq/master/nwr_v1_rc1_runtime_targeted_revision_v1_20260718/MANIFEST.json` is not runtime state.

## Runtime-owned authority

Repository contracts establish the exact ignored operational roots `local_exports/`, `draft_runtime_state/`, and `draft_day_runtime/` in `.gitignore`. `tests/hermetic_localdata_manifest.json` separately binds the only approved repository-local LocalData boundary to `local_exports`. The refresh orchestrator stores governed schema-v2 receipts below `local_exports/refresh_data`; the API settings default cache is below `local_exports/api_cache`. The draft runtime-state service owns `C:\NWR_SHARED_DATA\draft_runtime_state` and its `state`, `exports`, and `backups` children.

JSON files under those exact roots remain runtime state, including generic manifests, receipts, snapshots, caches, state files, archives, and nested files. A lookalike such as `local_exports_backup` receives no runtime authority.

## Unknown-path fail policy

Unknown JSON paths preserve the pre-existing fail-closed rule: a normalized path containing `runtime` or `draft_log` is runtime state. Unknown generic metadata basenames are not runtime solely because they are named `MANIFEST.json`, `manifest.json`, `metadata.json`, or `receipt.json`. Non-JSON paths remain outside this guardrail.

## Consequences and tests

A false positive makes Data Health RED and can reject an otherwise valid tracked evidence packet, as happened here. A false negative can hide tracked operational state and weaken local-first privacy and state separation. The contract therefore grants documentation relief only through exact root plus generic basename, grants runtime authority only through exact roots, and preserves fail-closed behavior elsewhere.

Focused tests cover the exact packet, generic/lowercase manifests, documentation receipts, actual operational manifests/receipts, nested roots, separators, case, traversal, lookalikes, ordinary files, and the prior missing/corrupt runtime-state behavior. The broad Data Health, receipt, passive-read, mutation, Refresh Recovery, and page-presentation suites remain green.
