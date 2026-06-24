# Prompt 01 - Persistent Draft State And Event Log

You are the Niners War Room Draft-Day App V2 Persistent Draft State + Event Log Lane Agent.

Repo:
`C:\NWR\Niners-War-Room`

Branch:
`work/hq-parallel-control`

Purpose:
Fix the P0 draft-day failure where a reload erased all drafted-player state. Implement local runtime autosave, reload restore, event log, export, and reset confirmation for Live Draft and Mock Draft. This is the foundation for later in-draft trades.

Hard guardrails:

- Do not mutate Frozen Final Draft Board V1.
- Do not change `final_board_rank`.
- Do not overwrite Dynasty Rank.
- Do not update `latest_candidate`.
- Do not update `latest_approved`.
- Do not mutate pinned snapshot.
- Do not change model/value/ranking logic.
- Do not change Mock Draft simulator value logic.
- Do not fabricate players, picks, ranks, trades, or probabilities.
- Do not use ADP, market rankings, projections, trade calculators, DynastyProcess values, or vendor ranks as model inputs.
- Do not track `C:\NWR_SHARED_DATA` files.
- No hosted deployment.
- Do not push unless explicitly approved after validation.

Runtime storage:

Use local-only runtime storage under:

`C:\NWR_SHARED_DATA\draft_day_runtime\`

This folder must never be committed.

Required features:

1. Autosave drafted picks.
   - When a player is assigned to a pick, write state to disk.
   - Include draft id, mode, source checkpoint, app commit if available, created/updated timestamps.

2. Reload restore.
   - On page load, restore saved state for active mode/draft id.
   - Drafted players remain drafted/hidden by default after reload.
   - Draft board restores assigned picks.

3. Event log.
   - Append an event for assign pick, undo, remove/edit assignment, reset, and export.
   - Event columns/fields should include timestamp, event_type, mode, draft_id, pick, player, position, team, before/after where practical, and notes.

4. Export draft log.
   - Export CSV.
   - Export JSON.
   - Export human-readable markdown recap.
   - Export files remain under `C:\NWR_SHARED_DATA\draft_day_runtime\exports\`.

5. Reset with confirmation.
   - User must explicitly confirm reset.
   - Reset clears runtime state for selected draft id/mode.
   - Reset writes a reset event before/with reset artifact when practical.

6. Live Draft and Mock Draft separation.
   - Live and Mock use separate namespaces or draft ids.
   - Mock Draft state must not contaminate Live Draft state.
   - Live Draft state must not contaminate Mock Draft state.

7. Source-truth safety.
   - No write to frozen board.
   - No write to source CSVs.
   - No latest file update.
   - All pick state is runtime/session/event-log only.

Likely files:

- `src/services/draft_day_workflow_service.py`
- new `src/services/draft_day_runtime_state_service.py`
- `app/components/draft_workflow.py`
- `app/pages/21_live_draft_room_v1.py`
- `app/pages/24_mock_draft_v1.py`
- `tests/test_draft_day_workflow_service.py`
- new `tests/test_draft_day_runtime_state_service.py`

Implementation notes:

- Prefer a small service layer with pure functions for serialization and validation.
- Use JSON as the canonical saved state format.
- Use CSV/JSON/MD for exports.
- Use atomic-ish writes where practical: write temp file, then replace.
- Include schema version.
- Include clear user-facing errors if runtime folder is unavailable.
- Keep UI compact.

Acceptance criteria:

- Assigning a player writes runtime state.
- Browser reload restores the assigned player and draft board.
- Undo after reload works.
- Remove/edit after reload works.
- Reset requires confirmation and clears runtime state.
- Export creates CSV/JSON/MD files in local runtime exports.
- Live and Mock states are separate.
- Frozen board remains 66 rows.
- Pinned hash unchanged.
- No `C:\NWR_SHARED_DATA` files tracked.

Validation:

- Focused pytest for runtime state service and workflow service.
- Ruff on touched files.
- Python compile/import checks.
- `git diff --check`.
- Browser proof:
  - open `/live-draft-room`
  - assign 1.01
  - reload browser
  - confirm drafted count and draft board restore
  - undo
  - reload
  - confirm undo persists
  - export draft log
  - reset with confirmation
  - open `/mock-draft`
  - confirm mock state is separate
- Confirm no source-truth/model/latest/pinned mutation.

Output doc:

Create/update:

`docs/hq/draft_day_v2/NWR_DRAFT_DAY_APP_V2_PERSISTENT_STATE_LANE_20260623.md`

Doc must include:

- verdict GREEN/YELLOW/RED
- runtime path
- state schema summary
- event types
- export files
- browser proof
- remaining caveats
- guardrail confirmation

Commit policy:

If validation is GREEN, commit locally with:

`Implement draft-day persistent state and event log`

Do not push unless Master explicitly asks.

Final response:

1. Final verdict GREEN/YELLOW/RED
2. Whether reload restore works
3. Runtime path
4. Event log/export result
5. Live vs Mock separation proof
6. Browser proof
7. Files changed
8. Tests/checks run
9. Commit hash if committed
10. Push status
11. Final git status
