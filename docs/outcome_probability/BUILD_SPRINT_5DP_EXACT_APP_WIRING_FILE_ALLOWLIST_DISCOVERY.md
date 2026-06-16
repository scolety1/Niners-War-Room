# Sprint 5DP: Exact App/Source/Test File Allowlist Discovery

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_EXACT_ALLOWLIST_APPROVED`

Sprint type: `DISCOVERY_AND_ALLOWLIST_ONLY_NO_APP_SOURCE_TEST_EDITS`

## 1. Scope

Sprint 5DP discovers and documents the exact file allowlist for the narrow non-numeric Outcome status implementation runway. This sprint did not edit app, source, or test files. It did not create app-readable outputs, current-player inference, current-player probabilities, exact display percentages, coarse display bands, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Inputs Reviewed

5DP reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5DG_PHASE_8_APP_WIRING_BOUNDARY_APPROVAL_PLAN.md`
- `docs/outcome_probability/BUILD_SPRINT_5DH_STATIC_APP_SURFACE_INVENTORY_SCHEMA_RISK_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5DI_NON_NUMERIC_STATUS_QA_CONTRACT_TEST_PLAN.md`
- `docs/outcome_probability/BUILD_SPRINT_5DJ_PHASE_8_APP_WIRING_PACKET_READINESS_VERDICT.md`
- `docs/outcome_probability/BUILD_SPRINT_5DK_PHASE_8_NARROW_APP_WIRING_IMPLEMENTATION_PROPOSAL.md`
- `docs/outcome_probability/BUILD_SPRINT_5DL_NON_NUMERIC_STATUS_CONTRACT_QA_FIXTURE_DESIGN.md`
- `docs/outcome_probability/BUILD_SPRINT_5DM_STATIC_NO_LEAKAGE_GUARD_HARNESS_PROTOTYPE.md`
- `docs/outcome_probability/BUILD_SPRINT_5DN_PHASE_8_CODE_TOUCH_APPROVAL_READINESS_VERDICT.md`
- `docs/outcome_probability/BUILD_SPRINT_5DO_FUTURE_APP_WIRING_PACKET_AND_ROLLBACK_CONTRACT.md`

Read-only source/test inspection included:

- `src/services/nwr_outcome_status_display_service.py`
- `tests/test_nwr_outcome_status_display_service.py`
- `app/pages/05_rankings.py`
- `tests/test_dynasty_rankings_page.py`
- `tests/test_outcome_column_integration_contract.py`

## 3. Discovery Result

The safest first code-touch step is a source-level Phase 8 status contract, not direct UI page display.

Reasoning:

- the existing app rankings page already has placeholder outcome columns and development copy, but row-level status display would risk table sorting, downloads, and fake precision before a safe source contract exists
- the existing `nwr_outcome_status_display_service.py` is tied to older status-only release-gate vocabulary and historical Sprint 5AH export helpers
- the Phase 8 vocabulary is narrower and different: `internal_review_passed`, `under_review`, `unavailable`
- a new narrow contract service can enforce vocabulary, eligible heads, unavailable fallback, and no numeric/sort/promotion fields without reading current-player data or local model artifacts
- UI page edits should remain deferred until the contract and no-leakage tests pass

## 4. Exact 5DQ Allowlist

5DQ may create/edit only:

- `docs/outcome_probability/BUILD_SPRINT_5DQ_NARROW_NON_NUMERIC_OUTCOME_STATUS_APP_WIRING.md`
- `src/services/nwr_outcome_phase8_status_contract_service.py`

5DQ may also edit this exact test file only if needed to keep the first code-touch sprint GREEN:

- `tests/test_nwr_outcome_phase8_status_contract_service.py`

No UI page/component file is allowed in 5DQ. If 5DQ needs `app/pages/05_rankings.py`, a player-detail component, table component, ranking service, or any app/source file not listed above, the packet must stop and report.

## 5. Exact 5DR Allowlist

5DR may create/edit only:

- `docs/outcome_probability/BUILD_SPRINT_5DR_NON_NUMERIC_STATUS_CONTRACT_TESTS_AND_STATIC_GUARDS.md`
- `tests/test_nwr_outcome_phase8_status_contract_service.py`
- `scripts/outcome_probability/audit_phase8_non_numeric_status_static_guard_v1.py`

5DR may edit this exact source file only if needed to make the tests pass without expanding scope:

- `src/services/nwr_outcome_phase8_status_contract_service.py`

No other test, script, app, or source file is allowed.

## 6. Explicitly Not Allowlisted

Not allowlisted for this runway unless a later sprint stops and HQ issues a new packet:

- `app/pages/05_rankings.py`
- `app/components/player_detail_card.py`
- `app/components/player_detail_panel.py`
- `app/components/tables.py`
- `src/services/table_sort_service.py`
- `src/services/ranking_surface_service.py`
- existing app loader or data-pack services
- any rookie file
- any `data/` file
- any `local_exports/` file

## 7. Required 5DQ Behavior

5DQ must enforce:

- approved status vocabulary only
- eligible heads only
- caution/deferred/blocked heads fail closed
- unknown or malformed status falls back to unavailable or raises validation error
- no current-player inference
- no app-readable generated data output
- no local model artifact reads
- no `data/` reads
- no `local_exports/` reads
- no probability, percentage, band, sorting, hidden-key, rank, score, or promoted artifact fields

## 8. Required 5DR Behavior

5DR must add tests/static guard coverage for:

- allowed vocabulary only
- eligible heads only
- excluded heads blocked
- unknown status fail-closed behavior
- absence of numeric probability/percentage/band fields
- absence of sorting/ranking/hidden-key fields
- absence of `data/`, `local_exports/`, model artifact, and current-player inference reads
- copy/UX text avoiding fake precision

## 9. Allowlist Verdict

5DP allowlist verdict: GREEN.

The safe file list is specific enough for 5DQ and 5DR. If any later sprint needs a file outside this list, the packet must stop.

## 10. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- read-only planning doc review completed
- read-only app/source/test inspection completed
- `git diff --check` passed

No Python files changed in 5DP, so `python -m py_compile`, Ruff, and pytest were not required.
