# NWR Draft-Day App V2 Lane Plan - 2026-06-23

This plan breaks Draft-Day App V2 into safe implementation lanes. Do not start coding from this plan until a lane prompt is explicitly issued.

## Lane 1: Persistent Draft State + Event Log

Purpose: Fix reload-loss failure and create the runtime foundation for every draft workflow.

Files likely touched:
- `src/services/draft_day_workflow_service.py`
- new `src/services/draft_day_runtime_state_service.py`
- `app/components/draft_workflow.py`
- `app/pages/21_live_draft_room_v1.py`
- `app/pages/24_mock_draft_v1.py`
- tests under `tests/`

Dependencies: none.

Acceptance criteria:
- Assigning a pick writes to local runtime storage.
- Reload restores picked players and draft board.
- Undo/edit/remove writes events.
- Export draft log works.
- Reset requires confirmation.
- Runtime path is `C:\NWR_SHARED_DATA\draft_day_runtime\`.
- Frozen board/source truth unchanged.

Tests/smoke:
- service tests for save/load/event ordering/reset/export
- app workflow tests for reload restore
- browser smoke Live Draft and Mock Draft

Guardrails: no source-truth mutation, no tracked runtime files, no rank/model logic changes.

Type: app + service.

## Lane 2: In-Draft Trade Events

Purpose: Allow pick ownership changes and future-pick recording during a live draft.

Files likely touched:
- draft runtime state service from Lane 1
- `src/services/draft_day_trade_event_service.py`
- `app/components/draft_workflow.py`
- Trading Lab page/components
- tests

Dependencies: Lane 1.

Acceptance criteria:
- User can record trade-away and trade-for events.
- Current-year pick ownership updates draft board.
- Future picks are stored in event log/sidebar.
- Example trade 1.04 for 2028 1st + 2.03 is supported.
- Event log export includes trade event.

Tests/smoke:
- trade event service tests
- browser proof of ownership update

Guardrails: no trade calculator/model advice; event log only unless later approved.

Type: app + service.

## Lane 3: Drafting Mode Shell / Navigation

Purpose: Separate Drafting Mode from Normal/Post-Draft Mode and make draft entry obvious.

Files likely touched:
- `app/navigation.py`
- `app/main.py`
- app shell components
- draft pages
- tests

Dependencies: Lane 1 preferred.

Acceptance criteria:
- Top-left Enter Draft Room button exists.
- User chooses Live Draft or Mock Draft.
- Drafting Mode has tabs: Cheat Sheets, Draft Board, Trade Lab, Player Compare, Search, Settings.
- Normal Mode remains available.
- Drafting Mode is focused and not cluttered.

Tests/smoke:
- navigation tests
- browser route smoke

Guardrails: no model/rank/source mutation.

Type: app.

## Lane 4: Player Compare Decision Summary

Purpose: Make Player Compare usable under pressure.

Files likely touched:
- player compare page
- compare service
- display components
- tests

Dependencies: none; can use Lane 1 state later for current pick context.

Acceptance criteria:
- Default compare starts with a concise decision summary.
- Detailed data moves behind tabs/expanders.
- Missing data says `Not enough information`.
- Injury/per-game/risk fields are shown only when available.
- Supports 2-4 players.

Tests/smoke:
- compare display tests
- browser compare proof with Jameson Williams vs Brian Thomas Jr if both available

Guardrails: no new model/rank logic; no fabricated injury conclusions.

Type: app.

## Lane 5: Trade Finder / Trade For

Purpose: Add decision-support tools for trading back or trading up during the draft.

Files likely touched:
- Trading Lab services/components
- new trade finder service
- draft runtime event service
- tests

Dependencies: Lanes 1 and 2.

Acceptance criteria:
- Trade Finder accepts current pick and suggests trade-back targets/packages conservatively.
- Trade For accepts target player/pick and suggests cheapest internal packages.
- Accepted trades write to event log.
- Outputs are decision support, not final trade advice.

Tests/smoke:
- trade package generation tests
- browser smoke for trade-back and trade-up flows

Guardrails: no external trade calculators as model inputs; display-only context labeled.

Type: app + model/data review.

## Lane 6: Injury + Per-Game Risk Modeling Audit

Purpose: Define and validate how NWR separates per-game performance, yearly totals, injury-shortened seasons, recovery risk, and chronic injury risk.

Files likely touched:
- docs first
- later model/source services only after approval
- tests if model service created

Dependencies: data-source accountability catalog.

Acceptance criteria:
- Injury/per-game/risk taxonomy is documented.
- Current sources and missing fields are audited.
- No player-facing injury score is created unless supported.
- Missing injury data is not treated as clean health.

Tests/smoke:
- docs/CSV validation
- source field tests if code added later

Guardrails: do not fabricate injury risk; do not scrape unsupported sources.

Type: data + model audit.

## Lane 7: Cheat Sheet / Tiered Board

Purpose: Build an overall-first draft cheat sheet with clear tiers and configurable density.

Files likely touched:
- Cheat Sheet page/component
- ranking display service
- tests

Dependencies: Lane 1 optional for current pick context.

Acceptance criteria:
- Overall ranking is the default.
- Tier separators are visually clear.
- Position views are secondary.
- User can choose number of players and note depth.
- Works when it is another team's pick.

Tests/smoke:
- display tests
- browser proof of tiers and filters

Guardrails: no rank changes; no hidden sort fields.

Type: app.

## Lane 8: Post-Draft Mode

Purpose: Separate post-draft review, roster implications, and next steps from live drafting.

Files likely touched:
- app navigation
- post-draft page/service
- draft log importer/reader
- tests

Dependencies: Lane 1.

Acceptance criteria:
- Draft log can be reviewed after draft.
- Drafted/passed players summarized.
- Trades made during draft summarized.
- No post-draft conclusions are treated as source truth without review.

Tests/smoke:
- draft log read tests
- browser post-draft smoke

Guardrails: no latest approval or ranking mutation.

Type: app + docs.

## Lane 9: Final Integration + Browser Acceptance

Purpose: Integrate completed lanes into one stable V2 app.

Files likely touched:
- app shell
- draft pages
- services
- docs
- tests

Dependencies: all implementation lanes.

Acceptance criteria:
- Full browser acceptance passes.
- Reload restore passes.
- Trade event example passes.
- Player Compare summary passes.
- Trade Finder/Trade For basic flows pass.
- Cheat Sheet tier display passes.
- Normal/Drafting/Post-Draft mode separation passes.
- No source-truth/rank/latest/pinned mutations.

Tests/smoke:
- focused pytest
- Ruff
- `git diff --check`
- browser route and interaction smoke

Guardrails: all global guardrails apply.

Type: integration.
