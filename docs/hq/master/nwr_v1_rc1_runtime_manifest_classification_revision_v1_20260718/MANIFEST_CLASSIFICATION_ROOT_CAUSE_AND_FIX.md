# Manifest classification root cause and fix

## Deterministic failure

The Data Health `No runtime JSON tracked` guardrail inspected repository-relative paths from `git ls-files`. Its filename heuristic treated any tracked JSON path containing `runtime` or `draft_log`, or ending in a generic operational-looking basename, as runtime state. The prior evidence packet directory contains `runtime` and ends in `MANIFEST.json`, so a tracked documentation manifest was misclassified. Hermetic consequently reported bootstrap 13/13, security 20/20, Python 2,626 passed / 1 failed, exit 1.

## Root cause

The rule combined a generic basename with substring matching and had no path-ownership model. It could not distinguish canonical HQ evidence from operational state. Renaming the required manifest, deleting the Hermetic assertion, or hardcoding one packet path would have hidden the defect rather than corrected it.

## Narrow correction

The classifier now normalizes complete path segments and applies ownership in this order:

1. Generic metadata below the exact tracked `docs/hq` root is documentation.
2. JSON below exact repository runtime roots or the absolute service-owned draft-runtime root is runtime state.
3. Unknown JSON paths retain the legacy fail-closed `runtime` / `draft_log` hint.
4. Generic basenames alone confer no runtime authority.

The order is intentionally narrow. A runtime-specific filename inside `docs/hq` remains fail closed, while lookalike documentation and runtime directories receive no special authority. Dot-segment normalization prevents traversal from borrowing either contract.

## Result and no-change boundary

The exact prior packet `MANIFEST.json` and the successor packet manifest are documentation. Manifests and receipts under approved runtime roots remain runtime state. Receipt schema version 2, closed fields, validation-before-mutation, privacy rejection, lifecycle, freshness, retained-data, last-known-good, refresh execution, Decision Trust Strip, Refresh Recovery, and page-open behavior are unchanged.

Focused classification/Data Health verification passed 34/34; the broad Data Health suite passed 142/142; clean-tree Hermetic passed 2,648/2,648 with exit 0.
