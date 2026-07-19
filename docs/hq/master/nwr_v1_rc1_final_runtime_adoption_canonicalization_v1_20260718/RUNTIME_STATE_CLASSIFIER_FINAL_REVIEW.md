# Runtime-state classifier final review

## Decision

The classifier is path-authority based. It is not a hardcoded exception for one file and does not classify a JSON path as runtime state solely from a generic basename.

The implementation normalizes separators and dot segments, applies supported-platform case normalization, and then evaluates repository-governed path ownership. The exact tracked path `docs/hq/master/nwr_v1_rc1_runtime_targeted_revision_v1_20260718/MANIFEST.json` is not runtime state. Generic `MANIFEST.json`, `manifest.json`, `metadata.json`, and `receipt.json` beneath the exact normalized `docs/hq/` authority are likewise excluded when no runtime authority owns them.

## Runtime authorities preserved

- repository-local `local_exports/`;
- `draft_runtime_state/`;
- `draft_day_runtime/`;
- the service-owned shared draft runtime root and its governed children.

Actual runtime manifests, receipts, nested runtime paths, and service-owned shared paths remain runtime state. Windows and POSIX separators classify equivalently. Case handling follows the supported Windows contract. Dot segments cannot escape ownership. Lookalike documentation and runtime roots gain no authority. Unknown JSON paths that carry existing runtime/draft-log fail-closed signals preserve that behavior.

Focused tests covered tracked documentation manifests, basename variants, governed receipts, nested paths, separators, case, dot segments, lookalike roots, shared-root ownership, and unknown JSON fail-closed cases. The exact 64-test combined route/classifier/lifecycle run passed, and the broader Data Health/core workflow suite also passed.

No change was observed in schema version 2 receipts, receipt privacy, validate-before-mutate, latest attempt/success/retained/stale/LKG semantics, Refresh Recovery, Decision Trust Strip, source admission, freshness policy, or passive page-read behavior.

Result: `PASS_PATH_OWNERSHIP_CLASSIFIER`.
