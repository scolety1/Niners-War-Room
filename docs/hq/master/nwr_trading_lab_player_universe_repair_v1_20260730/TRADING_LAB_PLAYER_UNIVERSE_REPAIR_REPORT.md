# Trading Lab 240-Player Universe Repair V1

Date: 2026-07-30

The bounded repair changes `/trading-lab` player authority from the frozen
66-row draft-board checkpoint to the existing, hash-validated 240-row Finished
V1 production universe. The frozen board remains available only for draft and
pick context.

Implementation commit: `500c69b44fec3382bd669c0a5b3fa603e9b1c6e8`

Implementation tree: `94af5c2ea002eef79f5cbb6acb244d9d85453902`

## Result

- Current-player selector: 240 rows and 240 unique `player_id` values.
- Exact ID parity: Finished V1 = player dimension = roster authority.
- Established-veteran proof: Patrick Mahomes (`player_id=4046`, Dynasty Rank 67)
  is selectable and is absent from the frozen 66-row board.
- Recent-rookie proof: Ashton Jeanty (`player_id=12527`, Dynasty Rank 46) is
  selectable and is absent from the frozen 66-row board.
- Picks: retained as a separate, display-only `pick_context:` identity lane.
- Labels: `Dynasty Rank`; missing ranks are disclosed as unavailable.
- Behavior: manual and descriptive only; no winner, recommendation, package
  valuation, Outcome V3 sorting, Dual-Lens value, or CFBD evidence.
- Failure behavior: invalid, incomplete, unapproved, or hash-invalid player
  authority stops the selector; the frozen board is never substituted.

The implementation changes only the Trading Lab page, its service, and focused
tests. Finished V1, Outcome V3, frozen comparators, active-pack data, providers,
and persistent state are unchanged.
