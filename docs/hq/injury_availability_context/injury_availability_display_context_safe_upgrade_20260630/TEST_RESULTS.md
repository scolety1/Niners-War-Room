# Test Results

Status: `PASS`

Focused validation run:

- Command: `python -m pytest tests/test_injury_availability_context_service.py tests/test_injury_context_source_gate_service.py tests/test_injury_context_flags_service.py tests/test_original_doc_remaining_ux_tools.py tests/test_dynasty_rankings_page_v1.py::test_rankings_default_preset_is_dynasty_review_clean_board tests/test_dynasty_rankings_page_v1.py::test_rankings_presets_and_advanced_filters_clean_top_controls`
- Result: `27 passed`

Static validation:

- Command: `python -m ruff check src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py`
- Result: `All checks passed`
- Command: `python -m py_compile src/services/injury_availability_context_service.py tests/test_injury_availability_context_service.py`
- Result: `PASS`

Final hygiene:

- Command: `git diff --cached --check`
- Result: `PASS`

Route smoke:

- Not required unless app pages are touched by this lane.
