# NWR Refresh Data Button And Orchestrator V1

Date: 2026-06-23

## What The Button Refreshes

The app now exposes a `Refresh Data` page/control immediately before `Mock Draft` in the visible Streamlit navigation. The button runs the central orchestrator in `src/services/data_refresh_orchestrator_service.py`.

Standard refresh runs:

- DynastyProcess market baseline into ignored local artifacts under `local_exports/refresh_data/dynastyprocess_market_baseline/latest`.
- Sleeper league-state snapshot into ignored local artifacts under `local_exports/refresh_data/sleeper`.
- Local status checks for runtime draft state, Model Evaluation Harness outputs, and Data Health inputs.

The optional slow-source checkbox can include the existing nflverse scheduled runner. It does not pass candidate-write flags.

## What It Does Not Refresh

The button does not mutate:

- Frozen Final Draft Board V1.
- `final_board_rank`.
- Dynasty Rank.
- tier assignments.
- `latest_candidate` or `latest_approved`.
- pinned snapshots.
- model/rank logic.
- runtime draft picks or trade decisions.

It does not make market, ADP, or DynastyProcess values model inputs.

## Source Registry

The orchestrator registry includes:

- `dynastyprocess_market_baseline`: public display-only market baseline, safe to run when the existing script is present.
- `sleeper_league_state`: public Sleeper league state, safe to run when the existing Sleeper runner/league configuration is present.
- `nflverse_refresh_runner`: existing public nflverse runner, skipped by default because it is slow and writes large shared snapshots.
- `nflverse_dataset_*`: dataset-level nflverse health rows for schema, coverage, freshness, missingness, row-count, and source-policy visibility. Missing dataset evidence is `Not enough information` or `NOT_CONFIGURED`, not zero/false/healthy/clean/no-role/no-injury/no-usage.
- `collegefootballdata`: key-gated, not run unless an approved app refresh connector is later registered.
- `rotowire_vendor_exports`: manual/vendor export only, blocked from button scraping.
- `gmail_league_history`: manual metadata/evidence queue only, raw email bodies are not pulled.
- `runtime_draft_state`: status check only.
- `model_evaluation_harness`: status check only.
- `data_health_inputs`: status check only.

## Status Meanings

- `GREEN`: refreshed or checked successfully.
- `YELLOW`: usable but review caveat.
- `RED`: attempted source failed.
- `SKIPPED`: intentionally skipped by refresh policy.
- `NOT_CONFIGURED`: no configured safe connector/script exists.
- `BLOCKED`: manual, vendor, email, or otherwise unsafe for button-driven refresh.

## Refresh Logs And Status

Refresh status is written to ignored local paths:

- `local_exports/refresh_data/latest_refresh_status.json`
- `local_exports/refresh_data/<run_id>_refresh_status.json`

Raw shared-data locations, if an existing source runner uses them, remain outside the repo under `C:\NWR_SHARED_DATA` and are not tracked.

## Privacy Guardrails

The button does not pull Gmail/email bodies, expose secrets, scrape blocked vendor sources, or commit refresh status/log files. CFBD remains blocked/not configured unless a specific approved connector is added later.

## Why Blocked Or Manual Sources Are Skipped

RotoWire/vendor data requires user-provided exports and source-term review. Gmail evidence requires explicit user review and must not ingest bodies from a general refresh control. CFBD requires API-key configuration plus an approved connector. These are reported clearly instead of being silently ignored.

## Tests And Checks

Focused coverage was added for:

- registry loading.
- not-configured safe skipping.
- blocked vendor non-execution.
- DynastyProcess path registration.
- failed-source isolation.
- result schema validation.
- ignored local status path.
- Data Health refresh-status consumption.
- rank/model/source-truth guardrails.
- navigation placement before Mock Draft.

## Browser Smoke

Browser smoke verified on 2026-06-24 with a local Streamlit server:

- `/rankings`
- `/cheat-sheets`
- `/drafting-mode`
- `/live-draft-room`
- `/player-compare`
- `/trading-lab`
- `/refresh-data`
- `/mock-draft`
- `/post-draft-mode`
- `/settings-data-health`

The root-loaded app showed `Refresh Data` before `Mock Draft`, no traceback, and no page-not-found fallback. The `Refresh Data` button completed without crashing, rendered the freshness summary/per-source results sections, and wrote ignored local status JSON showing DynastyProcess and Sleeper refreshed, nflverse skipped by default, CFBD not configured, and vendor/email sources blocked or manual.

## Known Limitations

- nflverse is skipped by default because the existing runner is slower and writes large shared snapshots.
- CFBD is not refreshed because no approved app connector is registered in this branch.
- Vendor and email sources remain manual by design.
- Standard refresh status tells the user what was refreshed; it does not promote any refreshed data into rank/model truth.
