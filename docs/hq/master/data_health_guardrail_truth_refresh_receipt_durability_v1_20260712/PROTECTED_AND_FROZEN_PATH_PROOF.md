# Protected and Frozen Path Proof

Starting baseline: `6bcb9c3c36fc560c30151591feaeff9d3960499f`.

The final changed-path scan is required to contain only the two approved pages, the bounded receipt component/service, truthful Data Health presentation/orchestrator receipt hook, focused tests/fixtures, and this documentation packet.

Required unchanged proofs:

- Refresh Recovery service/component Git blob hashes match the starting commit.
- Decision Trust Strip service/component Git blob hashes match the starting commit.
- No path matching frozen 2026 artifacts changes.
- No Player Compare or Trading Lab path changes.
- No ranking, formula, recommendation, source-registry definition, source-admission, plugin, rookie, roster-hydration, or draft-logic path changes.
- `source_governance_service.py` is unchanged.
- The orchestrator diff is limited to delegating post-run receipt persistence/loading; registry, selection, order, execution, retry, timeout, and source behavior are unchanged.
- No production dataset or local ignored receipt is tracked.

Final validation compares protected working-tree hashes against `git show HEAD:<path>`, scans the changed path list, and verifies `git ls-files local_exports/refresh_data` is empty.
