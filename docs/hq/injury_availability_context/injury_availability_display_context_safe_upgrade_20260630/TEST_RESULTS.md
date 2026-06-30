# Test Results

Status: `PASS`

Focused validation run:

- Command: `python -m pytest tests/test_injury_availability_context_service.py tests/test_injury_context_source_gate_service.py tests/test_injury_context_flags_service.py tests/test_original_doc_remaining_ux_tools.py tests/test_dynasty_rankings_page_v1.py::test_rankings_default_preset_is_dynasty_review_clean_board tests/test_dynasty_rankings_page_v1.py::test_rankings_presets_and_advanced_filters_clean_top_controls`
- Superseded by expanded command below.
- Command: `python -m pytest tests/test_injury_availability_context_service.py tests/test_injury_context_source_gate_service.py tests/test_injury_context_flags_service.py tests/test_original_doc_remaining_ux_tools.py tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_integrates_safe_rows_and_age_fallback tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_identity_review_rows_do_not_expose_details tests/test_nflverse_player_context_display_service.py tests/test_nflverse_refresh_health_service.py`
- Result: `39 passed`
- Command: `python -m pytest tests/test_dynasty_rankings_page_v1.py tests/test_original_doc_remaining_ux_tools.py`
- Result: `29 passed`

Static validation:

- Command: `python -m ruff check src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py`
- Expanded command: `python -m ruff check src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py app/pages/22_player_compare_v1.py`
- Result: `All checks passed`
- Command: `python -m py_compile src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py`
- Expanded command: `python -m py_compile src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py app/pages/22_player_compare_v1.py`
- Result: `PASS`

Final hygiene:

- Command: `git diff --cached --check`
- Result: `PASS`

Route smoke:

- Required because Player Compare is touched:
  - `/player-compare`: HTTP 200
  - `/rankings`: HTTP 200
  - `/settings-data-health`: HTTP 200
  - `/refresh-data`: HTTP 200

Streamlit smoke server:

- Command: `python -m streamlit run app/main.py --server.port 8515 --server.headless true --browser.gatherUsageStats false`
- Output after smoke: no runtime errors observed before shutdown.
