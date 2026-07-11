# Validation Results

## Verdict

`PASS_READ_ONLY_METADATA_SCAFFOLD_WITH_FAIL_CLOSED_MAPPING_CAVEAT`

The deterministic snapshot contains 1,269 artifact rows, 23 authority rows, 1,541 artifact lifecycle links, 30 unresolved duplicate/conflict objects, 40 no-recreate relationships, zero explicit source/use decision rows, zero real player rows, and zero real evidence-observation rows. Locality is exactly 1,085 `LIVE_HQ`, 162 `LOCAL_ONLY`, 3 `LOCAL_ONLY_RESTRICTED`, and 19 `OFF_HQ_BRANCH_ONLY`.

## Commands and totals

1. `git fetch --all --prune` — pass; controlling remote references refreshed.
2. `git rev-parse refs/remotes/origin/work/hq-parallel-control` — `e6d680195f9e4512885ac281c215f2fb2ae4b64c`.
3. `git log --reverse e6d680195f9e4512885ac281c215f2fb2ae4b64c..refs/remotes/origin/work/hq-parallel-control` — zero intervening commits; remote did not advance.
4. Git-blob SHA-256 verification with `git show HEAD:<manifest-entry-path>` — 21/21 consolidation packet entries and 12/12 canonicalization packet entries passed. Windows working-tree files are CRLF-materialized, so immutable Git-blob bytes, not checkout-normalized bytes, are the controlling hash input.
5. `python scripts/build_rookie_evidence_registry_scaffold_v1.py` — 1,269 artifact rows; 23 authorities; 1,541 lifecycle links; 30 duplicate/conflict objects; 40 no-recreate relationships; 0 explicit decisions.
6. `python scripts/validate_rookie_evidence_registry_scaffold_v1.py` — 118 checks, 0 issues, `PASS`.
7. `python -m pytest tests/test_rookie_evidence_registry_scaffold_v1.py -q` — 38 passed.
8. `python -m pytest tests/test_source_registry_service.py tests/test_source_governance_service.py tests/test_evidence_status_registry.py tests/test_data_health_dashboard_service.py tests/test_lifecycle_receipt_drilldown_service.py tests/test_lifecycle_audit_service.py -q --basetemp .codex-test-tmp/rookie-evidence-registry-regression` — 25 passed.
9. `python -m ruff check scripts/build_rookie_evidence_registry_scaffold_v1.py scripts/validate_rookie_evidence_registry_scaffold_v1.py src/services/rookie_evidence_registry_service.py tests/test_rookie_evidence_registry_scaffold_v1.py` — pass, 0 findings.
10. Python built-in `compile(...)` over the four new Python files — 4/4 passed without writing runtime state.
11. CSV/JSON parsing, schema/header, closed-enum, primary/foreign-key, duplicate-key, deterministic-order, artifact/locality reconciliation, manifest, authority, locator, decision, empty-player/evidence, duplicate/conflict, and no-recreate validation — included in the 118-check validator, 0 issues.
12. `rg` privacy/boundary scans over the workspace and documentation packet — 0 absolute-local-path matches; 0 raw restricted-scheme matches; 0 secret-pattern matches; 0 application imports; 0 read-only service write/network matches.
13. Locator semantic scan — 0 off-HQ active-use violations; 0 restricted reversibility violations.
14. Allowed-path, protected/frozen-path, ranking/formula/app/source-registry/plugin-governance diff scans — pass; only the scoped scaffold, build/validation helpers, read-only service, focused tests/fixture, and documentation packet are changed.
15. `git diff --check` and `git diff --cached --check` — pass before local commit.

## Boundary results

- Production authority true: 0/23.
- Player-value authority true: 0/23.
- Source-promotion decisions: 0.
- Identity resolutions: 0.
- Ranking/formula/training/production grants: 0.
- Evidence migration or mutation: 0.
- Runtime/application wiring: 0.
- Real player, alias, identity assertion, and evidence observation rows: 0 each.
- Synthetic fixture rows: 1 under `tests/fixtures` and excluded from all exports/counts.
- Frozen/protected file changes: 0.
- Privacy/rights expansion: 0.

The only substantive caveat is intentionally fail-closed: the design inventory supplies no exact artifact-to-authority/source/dataset/receipt foreign-key mapping at the required grain. Those optional links remain blank rather than being guessed. Missing decisions return `NOT_ENOUGH_INFORMATION` and the appropriate blocked/unadmitted evidence state.
