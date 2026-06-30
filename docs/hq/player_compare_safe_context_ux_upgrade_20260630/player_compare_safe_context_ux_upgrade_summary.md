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
- Activated a display-only `NFLVerse Player Context` tab backed only by the
  tracked player context display artifact and schema manifest.
- Added identity/join transparency, recent activity, usage/role, availability,
  roster-window, dataset freshness, and deferred/manual review expanders.
- Suppressed detailed NFLVerse context for `NEED_IDENTITY_REVIEW` rows.

## Implemented NFLVerse Context Display Pass

- Consumes only
  `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
  and the schema manifest in the same folder.
- Joins on `nwr_player_id`.
- Displays player context only for `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
  and `review_required=false`.
- Confirms displayed fields are `SAFE_NOW_DISPLAY_ONLY` in the schema manifest.
- Shows `Needs identity review` instead of player context details for review
  rows.
- Keeps missing values as `Not enough information`.

## Deferred

- Next game / opponent / bye context remains unavailable because the tracked
  artifact has `0` current/future safe schedule rows.
- Identity proposal rows remain manual-review-only and are not approved joins.
- `ff_rankings` remains blocked by source policy and unused.

## Blocked

No aggregate compare score, hidden sort, market decision logic, trade value,
pick value, injury-risk score, medical projection, comeback projection, rank
mutation, or source-truth promotion was implemented.
