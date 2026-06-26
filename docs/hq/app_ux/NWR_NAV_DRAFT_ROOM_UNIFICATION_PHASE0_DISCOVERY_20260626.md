# NWR Nav + Draft Room Unification - Phase 0 Discovery

## Verdict

GREEN.

Phase 0 inspected routing, navigation, draft-room pages, runtime-state helpers, tier-board surfaces, and existing tests before implementation edits.

## Current Structure

- Streamlit entrypoint: `app/main.py`
- Central navigation registry: `app/navigation.py`
- App shell and shared page header: `app/components/ui_framework.py`
- Live Draft route: `app/pages/21_live_draft_room_v1.py`
- Mock Draft route: `app/pages/24_mock_draft_v1.py`
- Drafting Mode cockpit route: `app/pages/19_drafting_mode_v2.py`
- Draft workflow component: `app/components/draft_workflow.py`
- Runtime state service: `src/services/draft_day_runtime_state_service.py`
- Existing legacy mock storage helper: `src/services/mock_draft_storage_service.py`
- Dynasty Rankings route: `app/pages/20_final_board_v1.py`
- Cheat Sheets route: `app/pages/18_cheat_sheets_v2.py`

## Findings

`app/navigation.py` is the correct place to implement the stable sidebar. `app/main.py` already uses `ALL_NAVIGATION_PAGES`, so a single shared nav can be achieved without page-by-page sidebar hacks.

`app/components/draft_workflow.py` already selects runtime mode from `session_key`: keys containing `live` use live state and keys containing `mock` use mock state. This makes it safe to preserve one draft-room engine for both Live Draft and Mock Drafts while extending the mock namespace carefully.

Live Draft V2 reliability is already integrated in the runtime service:

- missing state file produces explicit recovery status, not silent reset
- corrupt state is quarantined
- writes are atomic
- backups are created
- event log is persisted
- trade events update current-year pick ownership and store future picks
- export/import/restore uses preview and confirmation

Drafting Mode still has useful cockpit content: current pick, on-clock team, drafted/trade counts, autosave state, owned picks, recent events/trades, compact board, decision panel, and secondary tool links. That content should be moved or recreated inside Live Draft rather than kept as a primary route.

Mock Draft currently renders the same `render_draft_workflow` component as Live Draft, but it lacks named saved mock draft controls. Existing `mock_draft_storage_service.py` writes to `local_exports/mock_drafts`, which is not acceptable for this lane's runtime-state requirement. New mock draft management should use the local draft runtime root under `C:\NWR_SHARED_DATA` through `draft_day_runtime_state_service.py`, not `local_exports`.

Dynasty Rankings currently defaults to Full Dynasty Rankings, Dynasty Rank sort, and hidden market columns. That default must be preserved. A tier feature can be added as a display-only expander/view without changing rank, tier, sort, or market behavior.

Cheat Sheets should be removed from the primary sidebar but retained as a compatibility route.

## Implementation Plan

1. Add or update navigation tests and change `app/navigation.py` to expose the desired visible sidebar entries:
   - Live Draft
   - Mock Drafts
   - Dynasty Rankings
   - Player Compare
   - Trading Lab
   - Post-Draft Review
   - Future Tools
   - Refresh Data
   - Evidence Review
   - Settings / Data Health
2. Keep `/drafting-mode` and `/cheat-sheets` as hidden compatibility routes.
3. Add Live Draft command-center/banner content above the existing V2 workflow controls.
4. Convert `/drafting-mode` into a compatibility page that points users to Live Draft.
5. Add mock draft management helpers using runtime-root state namespaces and no `local_exports`.
6. Update Mock Drafts to use the same draft workflow plus named mock controls.
7. Add display-only tier summaries inside Live Draft and Dynasty Rankings.
8. Add a Future Tools roadmap-only page and nav entry.
9. Add focused tests for nav config, page banners, mock state separation, Future Tools, tier feature guardrails, and route compatibility.

## Guardrails

- No frozen board, rank, tier, latest, pinned, model, source-truth, CFBD/NFL, or decision-page wiring changes.
- No trade valuation.
- No market/ADP/DynastyProcess hidden sort or trade-value logic.
- No broad data refresh.
- No hosted deployment.
- Runtime files remain local-only and untracked.
