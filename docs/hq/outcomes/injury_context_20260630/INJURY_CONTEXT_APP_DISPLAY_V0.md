# Injury Context App Display V0

## Executive verdict

`GREEN_APP_DISPLAY_V0`

Injury Context Flags V0 is displayed as review-only context in:

- Dynasty Rankings: Outcome Lens only
- Player Compare: Injury / Availability Context panel

It is not displayed in Clean Board, Live Draft, Mock Draft, Trading Lab, hidden sort,
rank/model logic, trade value, or pick value.

## Artifact used

Enhanced Outcome V2 display artifact:

`docs/hq/outcomes/outcome_v2_horizon_20260630/outcome_v2_current_player_display_with_injury_context.csv`

Known artifact facts:

- 240 rows
- 201 prior-season injury context rows
- 5 missing current-feature rows
- 43 rookies/prospects out of scope

## Dynasty Rankings display

Surface:

`/rankings` -> `Outcome Lens`

User-facing callout:

`Injury context is review-only. No medical recovery projection is made. Missing injury context is not clean health.`

Visible labels:

- Injury Context Available
- Availability Caveat
- Limited Recent Sample
- Last Materially Active Season
- Seasons Since Material Activity
- Not Enough Information Reason

Clean Board does not include these columns.

## Player Compare display

Surface:

`/player-compare` -> `Injury / Availability Context`

User-facing callout:

`Review-only context. No medical projection or injury-risk score is made.`

For each compared player, the panel shows:

- Injury Context Available
- Availability Caveat
- Limited Recent Sample
- Last Materially Active Season
- Seasons Since Material Activity
- Not Enough Information Reason

Rows without a safe artifact match show:

`No approved injury context available. This does not mean clean health.`

## Example caveats

MarShawn Lloyd:

No approved 2025 Outcome V2 feature row remains `Not enough information`. Review-only
injury context shows 3 report weeks and 3 out/doubtful weeks in 2025. This is not a
medical projection and does not change Outcome probabilities.

Brandon Aiyuk, Joe Mixon, Tank Dell, and Jonathon Brooks:

No approved 2025 Outcome V2 feature row remains `Not enough information`. Missing injury
context is not clean health.

## Blocked uses

- Injury-risk score
- Medical recovery projection
- Comeback probability
- Hidden rank adjustment
- Dynasty Rank change
- Tier change
- Model input promotion
- Source-truth promotion
- Trade value
- Pick value
- Start/sit or waiver logic

## Future: Live Draft / Mock Draft injury context

Do not add injury context to Live Draft or Mock Draft yet.

Revisit only after rookie rankings and rookie outcome work are ready. A future
implementation should be a compact caveat chip or expander, not a draft-room ranking
modifier.

## Guardrails

- Outcome probabilities are unchanged.
- Missing values remain `Not enough information`.
- Rookies/prospects remain out of scope for normal Outcome V2.
- Missing injury context is not clean health.
- No app surface uses injury context for sort, rank, model input, trade value, or pick value.
- Live Draft and Mock Draft files are untouched.

## Human review checklist

- Confirm the caveat language is clear enough for draft-day use.
- Confirm the Outcome Lens table is not too wide for the intended device.
- Confirm Player Compare caveats help without implying medical certainty.
- Do not promote this context beyond display/review use without a new gate.
