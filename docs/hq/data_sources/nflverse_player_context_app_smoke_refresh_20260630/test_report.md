# NFLVerse Player Context App Smoke Test Report

Verdict: `GREEN_APP_SMOKE_REFRESH_CLEAN`

## Artifact And CSV Validation

Validation commands included:

```powershell
$py = 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m pytest ...
git diff --check
```

Observed artifact counts before docs creation:

- `nflverse_player_context_display_artifact.csv`: 294 rows
- `SAFE_NOW_DISPLAY_ONLY`: 281
- `NEED_IDENTITY_REVIEW`: 13
- `review_required=false`: 281
- `review_required=true`: 13
- newly activated rows matched in artifact: 41
- gated detail exposed: 0

## Focused Tests Run

Command:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_player_compare_nflverse_context.py tests/test_trading_lab_nflverse_context_service.py tests/test_development_lab_nflverse_context_service.py tests/test_draft_day_player_context_service.py tests/test_draft_day_player_context_ui_guardrails.py tests/test_injury_availability_context_service.py tests/test_nflverse_player_context_display_service.py tests/test_nflverse_schedule_context_display_service.py tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_integrates_safe_rows_and_age_fallback tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_identity_review_rows_do_not_expose_details tests/test_data_health_dashboard_service.py tests/test_data_refresh_orchestrator_service.py -q
```

Result: `94 passed in 8.13s`

Command:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_live_draft_room_page.py tests/test_drafting_mode_cockpit_page.py tests/test_mock_draft_room_service.py tests/test_post_draft_mode_service.py tests/test_navigation_compression.py -q
```

Result: `46 passed in 0.99s`

## Route Smoke

Temporary app server:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m streamlit run app/main.py --server.port 8523 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

All requested routes returned HTTP 200 and the Streamlit shell:

- `/player-compare`
- `/trading-lab`
- `/development-lab`
- `/live-draft-room`
- `/mock-draft`
- `/draft-analyzer`
- `/rankings`
- `/settings-data-health`
- `/refresh-data`

## Ruff And Python Compile

No Python files were touched in this verification lane, so Ruff and Python compile on touched Python are not applicable. Navigation-focused tests compiled registered page files.

## Code Change Status

No code changes.
