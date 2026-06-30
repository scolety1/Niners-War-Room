# Player Compare Safe Context UX Upgrade Summary

## Implemented SAFE_NOW

- Replaced the top `Decision Summary` framing with `Visible Context Summary`.
- Replaced answer-engine labels with `Visible-context read`,
  `Evidence coverage`, `Context note`, and `Open review flags`.
- Changed the service behavior so the top readout does not sort players into a
  hidden ladder or emit `Prefer <player>`.
- Preserved read-only rank context in visible rows without using it as an
  automatic recommendation.
- Removed market/ADP from top review flags and moved it below the summary as
  `Market timing context`.
- Removed pick-value display from Player Compare market context.
- Added cross-position readout: `Different positions / roster-fit decision`.
- Added multi-player copy: 3-4 player compares narrow review context and do not
  produce a final ranking or recommendation.
- Renamed judgment-like fields to `Stability evidence`, `Ceiling evidence`,
  `Roster-window context`, and `Main review flags`.
- Strengthened injury / availability copy while keeping it review-only.
- Added match-basis and fallback/ambiguity notes to injury availability rows.
- Added disabled/spec-only NFLVerse factual panel status rows.

## Deferred

All nflverse-dependent panels remain
`WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` because this branch does not contain a
merged dataset-level refresh-health green approval for those datasets.

## Blocked

No aggregate compare score, hidden sort, market decision logic, trade value,
pick value, injury-risk score, medical projection, rank mutation, or source-truth
promotion was implemented.
