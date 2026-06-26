# Codex Prompt B — NWR Live Draft V2 Reliability Lane

Use this only after Audit Intake + Guardrail Validation is complete, or if Tim explicitly chooses to start product reliability first.

## Goal

Build Live Draft V2 runtime reliability: persistent draft state, backups/recovery, draft event log, in-draft trade events, pick ownership updates, save/load/export/import, and post-draft audit support.

This is runtime/app reliability only. No model/rank/source-truth promotion.

## Starting point

Latest confirmed Master:

- Branch: `work/hq-parallel-control`
- HEAD: `16b78728cc11a66ba335308f028acf223002ca4a`

Use an isolated worktree/branch.

Recommended branch/worktree name:

- `work/live-draft-v2-reliability-20260626`
- `C:\NWR\Niners-War-Room-live-draft-v2-reliability-20260626`

## Inputs to read

- `03_LIVE_DRAFT_V2_REQUIREMENTS.md`
- `01_HQ_AUDIT_SYNTHESIS.md`
- `02_CONSOLIDATED_CODEX_ACTION_MATRIX.csv`
- existing Live Draft / Trading Lab / Post-Draft runtime services and tests

Known relevant areas from prior context may include:

- Live Draft Room page
- Trading Lab page
- Post-Draft Mode page
- `draft_day_runtime_state_service`
- runtime draft state paths
- tests for live/mock session separation
- any existing trade/event state helpers

Do not touch active NFL usage lane files unless this branch is explicitly assigned to that lane.

## Required implementation

### 1. Persistent runtime draft state

- Atomic writes.
- Timestamped backup/checkpoint before destructive writes.
- Missing/corrupt state cannot silently reset to empty.
- Recovery UI or safe service return that surfaces error and last valid backup.
- State survives Streamlit reload/browser refresh.
- State remains runtime-only and not source truth.

### 2. Draft event log

Add or harden append-only event log with event types:

- PICK_RECORDED
- PICK_UNDONE
- PICK_REMOVED
- PLAYER_REASSIGNED
- TRADE_RECORDED
- PICK_OWNER_CHANGED
- STATE_IMPORTED
- STATE_EXPORTED
- STATE_RESTORED
- MANUAL_CORRECTION

Each event should include timestamp, event_id, draft_id, event_type, payload, before/after state hashes or checkpoints, and notes where useful.

### 3. In-draft trade support

Support manual trade event builder:

- players
- current picks
- future picks
- pick ownership changes
- notes
- preview before apply
- undo/revert/audit

Acceptance example:

User can record giving `1.04` for `2028 1st` + `2.03`; the app updates pick ownership and records both current/future assets without changing ranks/model values.

### 4. Save/load/export/import

- Export current runtime state.
- Import with schema validation.
- Show preview before applying import.
- Require confirmation before overwrite.
- Backup current state before import.
- Bad import fails safely.

### 5. Post-Draft Mode audit support

- Recap picks/trades from event log.
- Show audit-only labels.
- Do not retrain or auto-promote evidence.

## Tests required

At minimum add tests for:

1. Missing state file.
2. Corrupt state file.
3. Backup creation on write.
4. Restore from backup.
5. Reload persistence.
6. Export/import round trip.
7. Import preview/confirmation path.
8. Trade event for 1.04 -> 2028 1st + 2.03.
9. Pick ownership update.
10. Future pick storage.
11. Multi-team or at least multi-asset trade.
12. Undo/replay consistency.
13. Protected artifact untouched.
14. Market/ADP values remain display-only and not used for trade/rank logic.

## Guardrails

Do not mutate:

- Frozen Final Draft Board V1
- `final_board_rank`
- Dynasty Rank
- tiers
- pinned snapshot
- `latest_candidate`
- `latest_approved`
- production model/rank logic
- source-truth/model-input gates

Do not use:

- DynastyProcess/ADP/market as hidden sort, trade value, or model input.
- CFBD/NFL/Gmail/vendor/proxy as model input.

Do not track raw/shared/local/secret paths.

## Validation to run

Run:

- `python -m pytest`
- `python -m ruff check .` if available
- relevant Streamlit/page smoke tests if available
- protected artifact diff check
- raw/secret tracked-file scan if available

## Final response format

Return:

1. Branch/worktree.
2. Commit hash.
3. Files changed.
4. Feature summary.
5. Test results.
6. Manual smoke instructions.
7. Guardrail confirmation.
8. Remaining limitations / next lane.
