# Validation Results

## Repository and source

- `git fetch --all --prune`: PASS.
- Live HQ resolve: `250c28853a4bc175b2702e206e68f49560c4e6e0`; expected value matched; no remote advance.
- Ancestry: source is a direct one-commit descendant of live HQ.
- `git merge --ff-only 46c19263df84015352e7a8bc6728507f48dc69ba`: PASS; source preserved exactly.
- Source inventory: 22/22 paths classified; no unrelated change.

## Tests and routes

- `python -m pytest -q tests/test_refresh_recovery_presentation_service.py tests/test_refresh_recovery_panel_render.py`: 5 passed.
- `python -m pytest -q tests/test_data_refresh_orchestrator_service.py tests/test_data_health_dashboard_service.py tests/test_source_governance_service.py tests/test_navigation_compression.py`: 50 passed.
- `python -m pytest -q tests/test_decision_trust_strip_service.py tests/test_decision_trust_strip_render.py tests/test_decision_trust_strip_surfaces.py`: 10 passed.
- Clean-HQ affected route smokes: 2 passed, zero exceptions.
- Source affected route smokes: 2 passed, zero exceptions.

## Static, semantic, and documentation

- Python `compileall` for all seven changed Python files: PASS.
- Ruff for all seven changed Python files: PASS.
- All eight states, precedence, stale retained data, partial success, gated/unavailable, failed/skipped, missing timestamp, diagnostic path, deterministic field order, and input immutability: PASS in focused tests and code review.
- Source packet committed-blob SHA-256 validation: 14/14 hashed artifacts passed. Windows worktree LF-to-CRLF normalization changes checkout byte hashes, so canonical committed blobs were used.
- Source packet CSV parsing: 5/5 passed.
- Glossary state uniqueness: 8/8; fixture state uniqueness: 8/8.
- Internal manifest paths: zero invalid.
- `git diff --check`: PASS; `git diff --cached --check` is rerun after staging this packet.

## Safety and presentation

- Passive adapter/component review: PASS.
- Recovery-action safety: PASS.
- Deprecation differential: baseline 11, source 11, new-code messages 0.
- Compact viewport 390 x 844: page horizontal overflow 0 px; focus visible; no focus trap; no executable panel actions.
- Frozen/protected/registry/admission/orchestration/freshness/model-output changed-path scans: all zero.
