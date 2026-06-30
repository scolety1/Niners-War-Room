# Test Results

Status: `PASS`

## Focused Validation

- Command: `python -m pytest tests/test_injury_availability_context_service.py -q`
- Result: `17 passed`

## Expanded Lane Validation

- Command: `python -m pytest tests/test_injury_availability_context_service.py tests/test_player_compare_safe_context_upgrade.py tests/test_player_compare_nflverse_context.py tests/test_original_doc_remaining_ux_tools.py tests/test_nflverse_player_context_display_service.py tests/test_nflverse_refresh_health_service.py tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_integrates_safe_rows_and_age_fallback tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_identity_review_rows_do_not_expose_details -q`
- Result: `44 passed`

## Static Validation

- Command: `python -m ruff check src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py`
- Result: `All checks passed`
- Command: `python -m py_compile src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py`
- Result: `PASS`
- Command: `git diff --check`
- Result: `PASS`

## Guardrail Scans

- Protected path scan excluding lane docs: no changed model, rank, source-truth, latest pointer, frozen board, draft, trade, pick, valuation, recommendation, tier, or probability path matched.
- Raw shared-data scan for `app/pages/22_player_compare_v1.py` and `src/services/injury_availability_context_service.py`: no `NWR_SHARED_DATA` references.
- Forbidden field scan: forbidden names appear only as blocked guardrail constants/tests/flags, not as active display fields or computations.

## Route Smoke

Streamlit command:

`python -m streamlit run app/main.py --server.port 8516 --server.headless true --browser.gatherUsageStats false`

Routes:

- `/player-compare`: HTTP 200
- `/rankings`: HTTP 200
- `/settings-data-health`: HTTP 200
- `/refresh-data`: HTTP 200

Server log check after smoke: no runtime errors observed before shutdown.
