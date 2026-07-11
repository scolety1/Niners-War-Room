# Validation Results

## Result

`PASS_PHASE_B_FAIL_CLOSED_DETERMINISTIC_LINKAGE`

- Frozen contract SHA-256: `19bb737de35f476ad39bff50d41f25e5ec6ef3b88dacd48d23b47917960fa264`.
- Artifact reconciliation: 1,269/1,269 unique rows.
- Active exact artifact→authority metadata links: 113.
- Verified/deferred candidates: 28 (25 dataset→source explicit-ID; 3 artifact→source exact-hash).
- Unresolved active-link gaps: 4,963.
- Canonical conflicting endpoint links: 0.
- Exact source/use decisions: 0.
- Active artifact authority/source/dataset/receipt foreign keys: 0.
- Real player, alias, identity-assertion, and evidence-observation rows: 0 each.

## Commands and totals

1. `python scripts/build_rookie_evidence_registry_linkage_gap_closure_v1.py` — deterministic counts above; no external access.
2. `python scripts/validate_rookie_evidence_registry_scaffold_v1.py` — 146 checks, 0 issues.
3. `python -m pytest tests/test_rookie_evidence_registry_scaffold_v1.py tests/test_rookie_evidence_registry_linkage_gap_closure_v1.py -q` — 53 passed.
4. Existing registry/governance/data-health/lifecycle regression selection — 25 passed.
5. `python -m ruff check` over six scoped Python files — 0 findings.
6. Python built-in `compile(...)` over six scoped Python files — 6/6 passed.
7. Phase B workspace/packet scans — 0 absolute-path, raw restricted-scheme, secret-pattern, and application-import matches.
8. Changed-path allowlist — 31 files, 0 out-of-scope, protected, or frozen paths.
9. Workspace and Phase B manifest validation — passed after final refresh.
10. `git diff --check` and `git diff --cached --check` — passed before local commit.

No authority, source admission, permission, player truth, evidence, identity, ranking, formula, production, application, plugin, protected, or frozen state changed. Phase B is local-only and is not pushed.
