# Mock Draft Simulator Service Contract

## Scope

The simulator service layer is local, deterministic, and review-only. It models
draft-room state transitions from fixture or local snapshot rows and must not
read live ADP, import production rankings, wire Streamlit UI, or promote
artifacts. No mock draft simulation should run until the required input
readiness checks are reviewed and accepted.

## State Inputs

- `pick_rows`: overall pick, round, round pick, pick label, current owner,
  original owner, and whether the pick is Niners-owned.
- `available_rows`: stable `asset_id`, player name, position, NFL team,
  asset type, lifecycle, local value fields already supplied by the fixture or
  snapshot, confidence, warning, rank, and range guidance.
- Optional market rows in simulator review scenarios are behavior-only context.
  They may affect opponent timing and availability review, never NWR quality or
  value.

Required inputs before any mock draft run:

- frozen rookie mock draft CSV;
- dropped, released, or otherwise available veteran pool;
- final pick order;
- NWR/my pick numbers;
- current rosters and keeper state;
- team needs and opponent tendency notes;
- NWR private value source;
- ADP/market source for opponent behavior only;
- manual review rules and stop conditions.

## State Transitions

- `create_empty_draft_state` builds the pick board and available pool, then
  validates duplicate pick/player identity and the current-pick pointer.
- `mark_player_drafted` records one selected player at a pick, removes that
  asset from the available pool, and recomputes the next open pick.
- `replace_drafted_player_at_pick` edits an already-filled pick, restores the
  prior player to the available pool, and rejects using a player already drafted
  at another pick.
- `undo_pick` restores the requested pick, or the latest drafted pick when no
  pick is supplied.
- `reset_mock` restores all drafted players to the available pool and returns
  the board to the first open pick.
- `draft_pick_history` returns deterministic pick-order history rows for local
  review surfaces and tests.

## Invariants

`validate_draft_state` reports issues without mutating state. Mutating service
entry points call the same invariant checks and fail fast when:

- draft picks are duplicated;
- available player assets are duplicated;
- drafted pick numbers are duplicated;
- drafted player assets are duplicated;
- a player asset is both available and drafted;
- a drafted pick is outside the pick board;
- `current_pick` no longer matches the first undrafted pick;
- `my_pick_numbers` no longer matches pick ownership flags;
- an explicit pick number is outside the draft board.

## Manual Validation Fallback

`pytest` and Ruff are the preferred commit-readiness gates. If they are not
available in the locked local environment, `scripts/mock_draft_state_smoke.py`
may be run as a pure-stdlib fallback for draft-state invariants. The fallback is
only a local safety signal; it does not make the lane fully commit-ready by
itself. Focused pytest and Ruff should still pass before final commit unless
Master explicitly accepts manual-smoke-only validation.

## Guardrails

- Do not import real ADP or market data in this layer.
- Do not use ADP/market context as NWR private quality or value.
- Do not touch Rookie formulas, Outcome logic, Drop Decision, app wiring, or
  promoted artifacts.
- Do not write generated simulator outputs outside ignored local-only paths.

## Non-Goals

- Production rankings or sorting.
- Outcome probabilities or probability bands.
- Streamlit/app wiring.
- Promoted or app-readable artifacts.
- Any final draft, keep, cut, or trade recommendation.
