# Test Report

Base and branch checks:

- `git fetch origin work/hq-parallel-control`: passed.
- Required minimum HQ commit: `2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0`.
- `git rev-parse origin/work/hq-parallel-control`: `2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0`.
- Required artifact scan: all requested refresh-health, player-context, identity-review, schedule-audit, service, and test artifacts found on `origin/work/hq-parallel-control`.
- `git merge --ff-only origin/work/hq-parallel-control`: passed after preserving first-pass Development Lab work.
- First-pass Development Lab work reapplied cleanly with `git stash pop`: no conflicts.

Artifact coverage confirmed:

- Player context artifact rows: 294.
- Safe display rows: 240.
- Identity review rows: 54.
- Identity proposals: 43, review-only.
- Human review identity rows: 4.
- `KEEP_NEED_IDENTITY_REVIEW` rows: 7.
- Schedule next game / opponent / bye: intentionally gated in Development Lab for a later lane-specific display review.
- `ff_rankings`: blocked.

Verification commands:

- `python -m compileall app src tests`: passed.
- `python -m pytest tests/test_development_lab_nflverse_context_service.py tests/test_development_lab_state_service.py tests/test_future_tools_rd_service.py tests/test_future_tools_page.py tests/test_nflverse_player_context_display_service.py tests/test_nflverse_refresh_health_service.py`: passed, 47 tests.
- `python -m ruff check app/components/development_lab.py app/pages/34_future_tools_v1.py app/pages/35_development_lab_v1.py app/pages/36_roster_weakness_tracker_v1.py app/pages/37_future_pick_planning_v1.py app/pages/38_keeper_deadline_prep_v1.py app/pages/39_drop_deadline_prep_v1.py app/pages/40_trade_deadline_prep_v1.py app/pages/41_upcoming_draft_prep_v1.py app/pages/42_draft_prep_compat_v1.py src/services/development_lab_nflverse_context_service.py src/services/development_lab_state_service.py src/services/future_tools_rd_service.py tests/test_development_lab_nflverse_context_service.py tests/test_development_lab_state_service.py tests/test_future_tools_rd_service.py tests/test_future_tools_page.py`: passed.
- `git diff --check`: passed; Git reported Windows LF-to-CRLF working-copy warnings only.
- Forbidden tracked path scan for raw/shared/cache artifacts: passed.
- Protected path/source-truth scan over changed files: passed.
- Banned active-language scan over Development Lab/Future Tools app/service files: passed.

Route smoke:

- `/development-lab`: passed, 0 exceptions.
- `/roster-weakness-tracker`: passed, 0 exceptions.
- `/upcoming-draft-prep`: passed, 0 exceptions.
- `/future-pick-planning`: passed, 0 exceptions.
- `/keeper-deadline-prep`: passed, 0 exceptions.
- `/drop-deadline-prep`: passed, 0 exceptions.
- `/trade-deadline-prep`: passed, 0 exceptions.
- `/future-tools`: passed, 0 exceptions.
- `/settings-data-health`: passed, 0 exceptions.

Route-smoke caveat:

- Existing Streamlit `use_container_width` deprecation warnings appeared during AppTest smoke.

Final safety verdict: `YELLOW_NEEDS_IDENTITY_REVIEW`.
