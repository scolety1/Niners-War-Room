# Sprint 5ER - Final Main Deploy-Readiness Smoke Test For Numeric Outcome Columns

## Scope

Sprint 5ER is the final deploy-readiness smoke gate for the Outcome numeric display work after `work/outcome-column-gate` was merged into `main`.

This sprint did not deploy, release, tag, merge, create new features, touch rookie files, create Top 6 or unapproved heads, create sorting/ranking effects, create hidden sort keys, or create promoted artifacts.

## Branch State

- Repository: `C:/Users/smcol/Documents/Vacation/Niners-War-Room-outcome`
- Branch: `main`
- Required merge commit present locally and on `origin/main`: `da1b491 Merge outcome numeric display gate`
- Initial status: `?? data/`

## Checks Run

- `git rev-parse --show-toplevel`: passed
- `git fetch origin`: passed
- `git checkout main`: passed
- `git status --short`: passed with only `?? data/`
- `git log --oneline -30`: confirmed `da1b491`
- `git log --oneline origin/main -10`: confirmed `da1b491`
- `.\.venv\Scripts\python.exe tests\test_nwr_outcome_numeric_probability_display_service.py`: passed, 7 tests
- `.\.venv\Scripts\python.exe tests\test_nwr_outcome_phase8_status_contract_service.py`: passed, 9 tests
- `.\.venv\Scripts\python.exe tests\test_nwr_outcome_phase9_status_release_gate.py`: passed, 7 tests
- `.\.venv\Scripts\python.exe tests\test_dynasty_rankings_page.py`: passed
- `.\.venv\Scripts\python.exe scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py`: `VERDICT=GREEN`
- `.\.venv\Scripts\python.exe scripts\outcome_probability\audit_phase9_outcome_status_release_gate_v1.py`: `VERDICT=GREEN`
- `.\.venv\Scripts\python.exe scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py`: `VERDICT=GREEN`
- `git diff --check`: passed

## Local Streamlit Smoke

Command used:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py --server.headless true --server.address 127.0.0.1 --server.port 8503 --browser.gatherUsageStats false
```

Local URL checked:

```text
http://127.0.0.1:8503/rankings
```

Result:

- Streamlit server started successfully on `127.0.0.1:8503`.
- HTTP request to `/rankings` returned `200`.
- Captured Streamlit logs showed the app URL and no traceback.
- Streamlit page test harness ran `app/pages/05_rankings.py` with zero exceptions.
- The selected `2026 Outcomes` view rendered the main Rankings dataframe with 232 rows.

## Visual Smoke Findings

Approved outcome columns appeared only after selecting the `2026 Outcomes` outcome-column view:

- `QB T12`
- `RB T12`
- `RB T24`
- `WR T12`
- `WR T24`
- `WR T36`
- `TE T12`

Column and value checks:

- No `Top 6` column appeared.
- No `QB T6`, `RB T6`, `WR T6`, `TE T6`, or `TE T3` column appeared.
- `player_id` was not visible in the rendered main dataframe.
- Readable percentage values appeared in approved columns.
- Unavailable/non-position rows used blank values rather than fake `0%` values.
- Fake `0%` count was zero across all approved outcome columns.
- The first five displayed players remained `Puka Nacua`, `Jaxon Smith-Njigba`, `Bijan Robinson`, `Jonathan Taylor`, and `Jahmyr Gibbs`, with ranks `1` through `5`.

Display-only checks:

- Phase 11 static guard confirmed `join_key=player_id_only`.
- Phase 11 static guard confirmed `top6_displayed=false`.
- Phase 11 static guard confirmed `name_based_join=false`.
- Phase 11 static guard confirmed `rank_sort_hidden_keys_created=false`.
- Phase 11 static guard confirmed `promoted_artifacts_created=false`.
- Existing tests confirmed outcome columns do not create sorting or hidden keys.

Layout checks:

- The local Streamlit page loaded successfully on the normal desktop URL.
- The main dataframe rendered without Streamlit exceptions.
- Narrow/mobile manual viewport inspection was not automated in this environment; no narrow-specific exception was observed in the app/test harness.

## Quarantine And Release Boundaries

- `data/` remained untracked and was not staged or committed.
- `local_exports/` was not staged or committed.
- `.venv/` was not staged or committed.
- No rookie files were touched.
- No deploy occurred.
- No release occurred.
- No tag was created.
- No Top 6 or unapproved heads were emitted or displayed.
- No sorting/ranking effects were created.
- No hidden sort keys were created.
- No promoted artifacts were created.

## Verdict

GREEN for final main deploy-readiness smoke.

Deploy/release/tag remains blocked until HQ separately authorizes the deploy/release step.
