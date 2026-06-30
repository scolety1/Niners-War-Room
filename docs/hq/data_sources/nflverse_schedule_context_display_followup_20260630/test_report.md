# Schedule Context Display Follow-up Test Report

Status: complete

## Focused Tests Run

`python -m pytest tests/test_nflverse_schedule_context_display_service.py tests/test_draft_day_player_context_service.py tests/test_development_lab_nflverse_context_service.py tests/test_trading_lab_nflverse_context_service.py tests/test_player_compare_nflverse_context.py`

Result: `34 passed`

## Relevant Surface Tests

`python -m pytest tests/test_nflverse_schedule_context_display_service.py tests/test_draft_day_player_context_service.py tests/test_draft_day_player_context_ui_guardrails.py tests/test_development_lab_nflverse_context_service.py tests/test_trading_lab_nflverse_context_service.py tests/test_player_compare_nflverse_context.py tests/test_player_compare_safe_context_upgrade.py tests/test_live_draft_room_page.py tests/test_live_draft_room_page_plan.py tests/test_drafting_mode_cockpit_page.py tests/test_mock_draft_room_service.py tests/test_draft_day_app_v1_service.py tests/test_injury_availability_context_service.py`

Result: `118 passed`

## Static Checks

- Ruff on touched Python: `passed`
- Python compile on touched Python: `passed`
- `git diff --check`: `passed`
- Forbidden tracked path scan on touched app/source files: `no matches`
- Protected behavior scan on touched app/source files: `no matches`

## Route Smoke

Temporary app URL: `http://localhost:8517`

HTTP smoke returned `200` for:

- `/player-compare`
- `/trading-lab`
- `/development-lab`
- `/live-draft-room`
- `/mock-draft`
- `/draft-analyzer`
- `/rankings`
- `/settings-data-health`

Browser smoke via system Chrome rendered the expected page text for all eight routes with no app exception text and no unfiltered console errors.

Observed non-blocking existing Streamlit warnings: `use_container_width` deprecation warnings. This lane did not address that app-wide cleanup.
