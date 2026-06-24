# NWR Trade Finder / Trade For V2 - 2026-06-23

## Verdict

GREEN for Phase 2 implementation.

The Trading Lab now has clearer conservative draft-day trade decision support. It remains a manual review workspace: no trade calculator was added, no model/value/rank logic changed, and accepted trades write only to the local Draft-Day V2 runtime event log.

## What Changed

- Trade Finder now uses the approved mock draft pick-order prop (`mock_draft/mock_pick_context.csv`) for current-year pick labels, owners, and NWR pick status.
- Trade Finder shows conservative trade-back target rows with:
  - current pick,
  - later target pick,
  - target owner,
  - what to ask for,
  - tier-drop risk,
  - nearby players who may still be available,
  - confidence,
  - caveat.
- Trade For now shows a compact acquisition row with:
  - target player,
  - pick to acquire,
  - current owner,
  - cheapest plausible internal package,
  - overpay warning,
  - worth-pursuing status,
  - confidence,
  - caveat.
- Accepted trade-back and trade-for events still write to the local V2 runtime event log through `record_trade_event`.

## Example Proof Scenario

The default Trade Finder workflow supports the required example:

- NWR sends: `1.04`
- NWR receives: `2.03 + 2028 1st`

The runtime service parses current-year pick ownership updates from `1.04` and `2.03`, records the future pick mention `2028 1st`, and includes the trade in the draft event log/export path.

## Guardrails

- Decision support only; no final trade advice.
- No external trade calculator.
- No private value.
- No hidden sort field.
- No source-truth mutation.
- No `final_board_rank` change.
- No frozen board mutation.
- Pick/order context and tier context are display-only.

## Remaining Caveats

- Trade Finder/Trade For are conservative heuristics from internal pick-order and visible board/tier context, not a solved trade market.
- DynastyProcess or other future market baselines must remain display-only unless a separate approved contract allows otherwise.
