# Live Draft V2 Reliability Requirements

## Why this is first

The real draft-day failure was not “bad rankings.” It was operational reliability:

- drafted/picked state was lost on reload
- in-draft trades were unsupported
- the app could not represent 1.04 traded away for a 2028 1st and 2.03
- there was no durable event log or backup/restore workflow

Live Draft V2 should fix state and trade reliability before any model/rank work.

## Non-goals

- No ranking changes
- No model changes
- No source-truth promotion
- No market/ADP-driven trade valuation
- No hidden sort changes
- No protected artifact writes

## Required runtime state behavior

Runtime draft state must be local/runtime only and explicitly not source truth.

It must support:

- draft_id
- league/scoring metadata snapshot label
- picked/drafted players
- pick order
- pick ownership
- my picks/upcoming picks
- trade events
- undo/remove/reassign events
- import/export metadata
- source checkpoint/hash if available
- created_at / updated_at
- schema_version

## Persistence requirements

- Atomic writes.
- Timestamped backup before every destructive write.
- Recovery if state file is missing/corrupt.
- No silent reset to empty state.
- Export/import round trip.
- Import preview before overwrite.
- Confirmation checkbox before applying import.
- State survives Streamlit reload/browser refresh.
- Corrupt state is quarantined, not overwritten.

## Event log requirements

Each event should include:

- event_id
- timestamp
- draft_id
- event_type
- actor/source
- payload
- before_state_hash
- after_state_hash
- notes
- schema_version

Event types should include:

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

## Trade event requirements

Manual trade event builder must support:

- current picks
- future picks
- players
- FAAB/cash placeholder only if app already supports it
- multi-team trades if feasible
- notes
- draft board ownership preview
- apply / cancel
- undo/revert

Required acceptance example:

- User records: give 1.04, receive 2028 1st + 2.03.
- Draft board updates ownership of 1.04 and 2.03.
- 2028 1st is stored as future pick asset.
- No ranking/model/value changes.
- Event appears in post-draft recap.
- User can undo or audit the change.

## Test plan

Minimum tests:

1. Missing runtime state file does not silently reset without warning.
2. Corrupt runtime state file offers restore from backup.
3. Every state write creates a checkpoint.
4. Browser reload preserves drafted/picked players.
5. Export/import round trip returns equivalent state.
6. Import preview blocks overwrite without confirmation.
7. Trade event updates pick ownership.
8. Future-pick trade is stored and displayed.
9. Multi-team trade does not corrupt ownership.
10. Undo/replay reconstructs expected state.
11. Runtime state stays out of model/source-truth directories.
12. Protected artifact diff check remains clean.
