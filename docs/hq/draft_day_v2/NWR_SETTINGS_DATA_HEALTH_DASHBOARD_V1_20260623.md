# Settings / Data Health Dashboard V1

Date: 2026-06-23
Branch: work/hq-parallel-control
Verdict: GREEN

## What Changed

Created a Settings / Data Health dashboard backed by a reusable service:

- `src/services/data_health_dashboard_service.py`
- `app/pages/28_settings_data_health_v1.py`

The canonical dashboard route is now:

- `/settings-data-health`

The existing route remains available:

- `/settings`

## What The Dashboard Shows

The dashboard summarizes:

1. App/version status
   - current git HEAD
   - branch
   - app mode
   - generated timestamp
   - source badge

2. Board health
   - frozen baseline board row count, expected 66
   - pinned hash status
   - `latest_candidate` / `latest_approved` guardrail status
   - full dynasty rankings row count, expected 240
   - known caveat: approved full dynasty source currently has 0 rookie/prospect rows

3. Market baseline health
   - DynastyProcess freshness
   - upstream scrape date
   - fetch timestamp
   - market player row count
   - market join coverage
   - display-only guardrail label

4. Runtime draft state health
   - runtime state path
   - latest live/mock state presence
   - latest live update timestamp
   - drafted player count
   - trade event count
   - backup count
   - manual/local runtime-state warning

5. Historical/model evidence health
   - ACTUAL_DROP truth bucket count
   - INFERRED_DROP caution bucket count
   - PROXY sensitivity bucket count
   - proxy rows not training truth
   - model evaluation warning count
   - no unsupported predictive accuracy claim

6. Missing-data health
   - high-priority missing league-history items
   - actual 2026 draft log imported status
   - trade history imported status
   - Gmail evidence queue status

7. Guardrail checklist
   - market display-only
   - frozen board baseline/checkpoint wording
   - no raw shared data tracked
   - no runtime JSON tracked
   - no source-truth mutation
   - no model/rank mutation

## Data Sources Used

- Draft-day app service board loaders
- DynastyProcess market baseline service
- Draft-day runtime state service
- Model Evaluation Harness V0 outputs
- League-history evidence backlog and normalized intake files
- Git status/listing checks for tracked-file guardrails

## Guardrail Meanings

- GREEN: usable or confirmed safe.
- YELLOW: usable with review caveat; do not ignore the note.
- RED: do not trust that area until repaired.

Market/DynastyProcess context remains display-only and is not used as model truth. Runtime state is manual/local draft session data and is not official source truth.

## Known Caveats

- Overall dashboard status is expected to be YELLOW while known data caveats remain.
- Approved full dynasty source is 240 rows but currently has 0 rookie/prospect rows.
- League-history hard inputs are still missing: actual 2026 draft log and Sleeper trade export.
- Gmail evidence remains review-only metadata; raw email bodies are not tracked.
- Runtime state may be absent on a fresh machine or in mock mode until the user saves/records events.

## Tests / Checks

Passed:

- `pytest tests/test_data_health_dashboard_service.py`
- `ruff check src/services/data_health_dashboard_service.py app/pages/28_settings_data_health_v1.py tests/test_data_health_dashboard_service.py`
- `py_compile` on touched Python files
- `git diff --check`

Focused service tests cover:

- frozen board row-count check
- full dynasty row-count check
- market freshness loading
- runtime state health with no state
- runtime state health with sample state
- historical drop bucket counts
- proxy-only warning
- missing-data warnings
- no tracked shared/runtime files

## Browser Smoke

Routes smoked:

- `/settings-data-health`
- `/settings`
- `/rankings`
- `/live-draft-room`
- `/cheat-sheets`
- `/post-draft-mode`
- `/player-compare`
- `/trading-lab`
- `/mock-draft`

Expected dashboard proof:

- compact status cards render near the top
- warning summary is visible when YELLOW items exist
- details are in expanders
- frozen baseline rows show 66
- full dynasty rows show 240
- market baseline says display-only
- runtime state says manual/local, not official source truth

## Future Improvements

- Add direct links from each warning to the relevant source/report.
- Add a downloadable health snapshot.
- Add timestamped health-history trend output if Master approves tracked summary artifacts.
- Add explicit RC audit status ingestion if the release-candidate audit becomes machine-readable.
