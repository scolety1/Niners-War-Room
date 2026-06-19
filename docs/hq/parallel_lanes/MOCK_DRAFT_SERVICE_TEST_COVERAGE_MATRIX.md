# Mock Draft Service Test Coverage Matrix

| Area | Test File | Validation Command | Status | Fixture Only | Writes Files | Can Run Simulations | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Draft state service | `tests/test_draft_state_service.py` | `pytest tests/test_draft_state_service.py` | GREEN | Yes | No | No | State invariants and undo/reset behavior. |
| Input contracts | `tests/test_mock_draft_input_contract.py` | `pytest tests/test_mock_draft_input_contract.py` | GREEN | Yes | No | No | Role schemas and source separation. |
| Manifest contract | `tests/test_mock_draft_input_manifest.py` | `pytest tests/test_mock_draft_input_manifest.py` | GREEN | Yes | No | No | Fixture manifest validation. |
| Available pool contract | `tests/test_mock_draft_available_pool_contract.py` | `pytest tests/test_mock_draft_available_pool_contract.py` | GREEN | Yes | No | No | Duplicate and identity checks. |
| Pick order contract | `tests/test_mock_draft_pick_order_contract.py` | `pytest tests/test_mock_draft_pick_order_contract.py` | GREEN | Yes | No | No | Pick-number and my-pick validation. |
| Roster contract | `tests/test_mock_draft_roster_contract.py` | `pytest tests/test_mock_draft_roster_contract.py` | GREEN | Yes | No | No | Keeper and available-overlap checks. |
| Team needs contract | `tests/test_mock_draft_team_needs_contract.py` | `pytest tests/test_mock_draft_team_needs_contract.py` | GREEN | Yes | No | No | Opponent behavior only. |
| Market separation | `tests/test_mock_draft_market_separation_contract.py` | `pytest tests/test_mock_draft_market_separation_contract.py` | GREEN | Yes | No | No | ADP/market never NWR value. |
| Readiness renderer | `tests/test_mock_draft_readiness_report.py` | `pytest tests/test_mock_draft_readiness_report.py` | GREEN | Yes | No | No | Human-readable preflight. |
| Diagnostics/aliases | `tests/test_mock_draft_schema_diagnostics.py`, `tests/test_mock_draft_header_aliases.py` | focused pytest | GREEN | Yes | No | No | Header and contamination checks. |
| Real-input bridge | `tests/test_mock_draft_manifest_bootstrap.py`, `tests/test_mock_draft_template_renderer.py`, `tests/test_mock_draft_real_input_preflight.py`, `tests/test_mock_draft_redaction.py` | focused pytest | GREEN | Yes | No | No | Dry-run/local-only scaffolding. |
| Closeout status | `tests/test_mock_draft_closeout_status.py` | `pytest tests/test_mock_draft_closeout_status.py` | GREEN | Yes | No | No | Handoff summary script. |
| No-real-data audit | `tests/test_mock_draft_no_real_data_committed.py` | `pytest tests/test_mock_draft_no_real_data_committed.py` | GREEN | Yes | No | No | Committed docs/fixtures guardrail. |
