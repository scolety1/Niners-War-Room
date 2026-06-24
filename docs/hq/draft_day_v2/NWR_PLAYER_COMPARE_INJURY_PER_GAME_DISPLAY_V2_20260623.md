# NWR Player Compare Injury / Per-Game Display V2 - 2026-06-23

## Verdict

GREEN.

Player Compare now includes a display-only `Injury / Per-Game Context` tab below the main decision summary. It uses the completed audit CSV and does not create an injury score, rank adjustment, model value, hidden sort, or medical conclusion.

## What Was Added

- A new Player Compare detail tab: `Injury / Per-Game Context`.
- Clear label:
  - `Display-only context. Not used to change rank or model value.`
- Per-player fields:
  - `Per-Game Signal Available`
  - `Annual Total Signal Available`
  - `Injury Data Available`
  - `Current Injury Status`
  - `Recovery Risk Band`
  - `Chronic Injury Risk Band`
  - `Human Review Warning`
  - `Model Treatment Summary`
  - `Annual Totals Warning`
- Compact warning when the audit says annual totals may mislead because availability/games context is incomplete.

## Missing-Data Behavior

Missing or unsupported fields show exactly:

`Not enough information`

The display explicitly warns that missing injury coverage does not mean clean health.

## Proof Cases

Browser smoke targets:

- `Jameson Williams` vs `Brian Thomas`
- `Tyreek Hill` vs `Keenan Allen`
- `Darren Waller` with another player if available
- One rookie from `Jeremiyah Love`, `Makai Lemon`, `Carnell Tate`, `KC Concepcion`, `Jadarian Price`

Expected behavior:

- Decision Summary remains first.
- Injury/per-game context is behind a tab below the summary.
- Missing current injury/recovery/chronic data displays `Not enough information`.
- No source-truth or rank/model logic changes.

## Guardrails

- No frozen board mutation.
- No `final_board_rank` change.
- No Dynasty Rank overwrite.
- No `latest_candidate` or `latest_approved` update.
- No pinned snapshot mutation.
- No injury score created.
- No fabricated injury status, recovery risk, chronic risk, or medical conclusion.
- No `C:\NWR_SHARED_DATA` files tracked.

## Remaining Caveat

The audit verdict remains YELLOW: current injury/games-missed/recovery coverage is insufficient for automated modeling. This UI section is strictly display-only context.
