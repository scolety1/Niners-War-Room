# Development Lab Safe V1 Persistence

Date: 2026-06-27

## Purpose

Development Lab Safe V1 adds local reload-safe persistence for manual Development Lab tools. This fixes the Safe V0 caveat where manual notes existed only in the current page session unless exported.

This is not model input, not source truth, not a rank update, and not draft-room runtime state.

## Completed Pages

Local lab-state controls were added to:

- `/upcoming-draft-prep`
- `/future-pick-planning`
- `/roster-weakness-tracker`
- `/keeper-deadline-prep`
- `/drop-deadline-prep`
- `/trade-deadline-prep`

`/development-lab` now shows a simple saved-state status table for each Safe V0 tool:

- No saved notes
- Saved locally
- Last updated timestamp
- Local path

## Local State Path

Default local root:

`C:\NWR_SHARED_DATA\development_lab_state`

Runtime/test override:

`NWR_DEVELOPMENT_LAB_STATE_ROOT`

State files are local-only and must remain untracked. The app does not write user-entered lab notes into the repo.

## Persistence Behavior

Each tool has a stable key:

- `roster_weakness_tracker`
- `future_pick_planning`
- `upcoming_draft_prep`
- `keeper_deadline_prep`
- `drop_deadline_prep`
- `trade_deadline_prep`

Each tool supports:

- load saved local state on page open
- save current manual fields
- export current state as JSON
- import JSON with preview
- blocked import until explicit confirmation
- reset saved state only after explicit confirmation

## Backup / Import / Reset Behavior

Before overwrite, reset, or confirmed import, the service creates a timestamped backup under:

`C:\NWR_SHARED_DATA\development_lab_state\backups`

If a saved JSON file is corrupt, it is quarantined under:

`C:\NWR_SHARED_DATA\development_lab_state\corrupt`

Corrupt state is not silently treated as clean state or source truth.

## What This Does Not Do

This lane does not:

- touch Live Draft Room
- touch Mock Drafts
- touch draft runtime state service
- touch draft workflow or pick ownership
- change Dynasty Rankings
- run data refresh
- change model/rank/source-truth logic
- create start/sit, waiver, trade target, rookie class, pick value, or trade value logic
- promote CFBD, NFL usage, DynastyProcess, ADP, Gmail, vendor, proxy, or Outcome data

## Guardrails

All persisted lab notes remain:

- local-only
- manual/display-only
- untracked
- not source truth
- not model input
- not training truth
- not decision-page wiring

## Remaining Caveats

The save/import/reset controls are intentionally simple. They preserve manual notes, but they do not sync across machines, resolve conflicts, or validate whether a note is accurate.

Future improvements should stay in this lane unless explicitly approved:

- clearer per-tool saved-state badges
- optional package export of all lab notes
- visual restore-from-backup selector
- broader UI click-through tests
