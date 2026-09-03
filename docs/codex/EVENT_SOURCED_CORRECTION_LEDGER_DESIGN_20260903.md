# Event-sourced draft correction ledger — design (2026-09-03)

Design only, not implemented tonight -- this touches the same live
pick-recording path Lane B and Lane C changes landed in earlier this
session, and deserves its own focused, separately-tested pass rather than
a rushed addition at the end of a long one.

## Current state (traced to code, not assumed)

Two layers, both LIFO-only:

- `src/services/redraft_engine_v1_service.py`: `mark_player_drafted()` /
  `undo_last_draft_pick()` -- a flat `drafted: [...]` id list; undo pops
  the last id.
- `src/services/redraft_draft_room_v1_service.py`: `_record_pick()`
  appends a rich record (`pick_number, round, team_slot, player_id,
  player_name, position, team, actor, selection_behavior, nwr_rank,
  picked_at_utc`) to `state["picks"]`; `undo_room_pick()` pops the last
  entry and rebuilds `drafted` from what remains.

Neither layer can correct an arbitrary earlier pick without discarding
and re-entering every pick after it. This is the real gap section 13 (and
the reconciliation ledger's `EXACT_MATCH`/`SEARCH_FAILURE` split) is
asking to close -- an operator who mis-recorded pick 83 five rounds ago
currently has no way to fix it without re-doing everything since.

## Proposed model

Stable per-slot identity (matches the brief's field list exactly):

```
pick_id        stable, assigned once per (round, team_slot) at draft
                start -- never reused, never renumbered
pick_number    display-only, derived from round/team_slot/draft order
round          fixed at draft start
team_id        fixed at draft start (team_slot)
player_id      nullable -- null means UNRESOLVED
status         RESOLVED | UNRESOLVED
source         OWNER_MANUAL | SLEEPER_READ_ONLY | CPU_MOCK | CORRECTION
recorded_at    utc timestamp of the most recent write to this slot
revision       increments on every write to this slot
```

This is a small but real reframe from the current model: today
`state["picks"]` is an *append log of events*, and "the board" is derived
by taking the whole log in order. The proposal keeps the append log
(useful audit trail, and section 24's NWR PURE 001 decision-receipt
requirement wants exactly this) but adds a **projected, slot-keyed
current-state view** (`pick_id -> current record`) that a correction can
target directly, instead of requiring the log's tail to be the only
mutable point.

### Operations

- **REPLACE PICK** (`pick_id`, `new_player_id`): append a `CORRECTION`
  event referencing `pick_id`; recompute the slot-keyed view (`player_id`
  swaps, `revision += 1`); old player returns to the available pool, new
  player leaves it. Every other slot's `pick_id`/`round`/`team_id`/
  `pick_number` is untouched -- this is the core acceptance requirement
  ("later picks stay intact").
- **CLEAR PICK** (`pick_id`): append a `CORRECTION` event setting
  `player_id = null`, `status = UNRESOLVED`. Slot, round, team, and
  pick_number are preserved -- nothing shifts.
- **FILL GAP** (`pick_id`, `player_id`): identical mechanism to REPLACE,
  just starting from `status=UNRESOLVED` instead of a wrong player. Same
  code path, not a special case.
- **UNDO**: reverses only the single most recent `CORRECTION` (or
  original recording) event, by `pick_id`, not globally-LIFO across the
  whole draft -- this is the one real behavior change from today's
  `undo_room_pick`, which is LIFO over the *entire* draft rather than
  per-slot. Needs its own explicit design conversation: does "undo" mean
  "undo my last correction anywhere" (current global-LIFO semantics,
  extended) or "undo the last change to *this* slot"? The brief's
  acceptance list ("reverse latest action only") reads as the former;
  flagging the ambiguity rather than picking one silently.

### Legality/collision rules

- REPLACE/FILL GAP must reject a `player_id` already assigned to a
  *different* `pick_id` with `status=RESOLVED` (no double-drafting a
  player) -- this validation already exists in spirit
  (`owner_pick_and_advance`'s "already drafted" check) and should be
  reused, not reimplemented.
- CLEAR must not be reachable on a slot that's already `UNRESOLVED`
  (no-op, not an error, but shouldn't create a spurious ledger event).
- All three must preserve `ingest_read_only_sleeper_pick`'s existing
  fail-closed pick-number-skew check for the LIVE_READ_ONLY sync path --
  a correction event is a distinct code path from live sync ingestion and
  must not be reachable by it.

## Storage

Additive to the existing `draft_boards/<profile_id>.json` file (same
atomic temp-then-replace pattern already used by
`load_draft_board`/`_atomic_json`), not a new file/store -- avoids
introducing a second source of truth for board state. Append the full
correction event list under a new `corrections: [...]` array alongside
the existing `picks: [...]` log; the slot-keyed projected view is
computed at read time from `picks` + `corrections` in order, not stored
separately (keeps the file the single source of truth, matches the
existing "never mutate source, only append" checkpoint-fix philosophy
from earlier this session).

## Acceptance tests this should ship with (not yet written)

Matches the brief's list directly: correct a pick one round back; five
rounds back; a Round 1 correction applied late in a 12-round draft;
clear-then-fill on the same slot; a collision attempt (drafting an
already-rostered player) rejected; and confirming a corrected board,
closed and reopened, persists the correction (not just in-memory).

## Why this is a design doc, not a diff, tonight

`_record_pick` / `owner_pick_and_advance` / `undo_room_pick` are exactly
the functions Lane B and Lane C's real-money changes landed near tonight.
Stacking a third structural change to the same live pick-recording path
in one session, untested against the correction-specific acceptance list
above, is the kind of scope-stacking that produces exactly the class of
defect this whole session's KHA postmortem was about. This is ready to
implement next -- same worktree, same tests-first process this session
used for Lane B/C -- but as its own pass.
