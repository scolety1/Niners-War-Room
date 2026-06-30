# NFLVerse Availability Guardrail Audit

Verdict: `PASS`

## Identity And Denominator Gates

Detailed NFLVerse availability context displays only when:

- player context joins by `nwr_player_id`
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- the displayed player-context field has `field_status=SAFE_NOW_DISPLAY_ONLY`
- denominator detail comes from a row with `denominator_status=SAFE_NOW_DISPLAY_ONLY`
- the denominator field is schema-approved for display-only use

Rows with `NEED_IDENTITY_REVIEW` or `NEED_IDENTITY_APPROVAL` show review or
missing status only. They expose no roster, injury, snap, stat, denominator, or
schedule detail.

## Missing Data Rules

- Missing injury report status is not healthy.
- Missing roster status is not clean, safe, active, or inactive.
- Missing weekly roster status is not clean, safe, active, or inactive.
- Missing snap data is not zero.
- Missing stat data is not zero.
- Missing denominator rows are not zero-game rows.
- Missing schedule context is not a bye or no game.
- Missing values display as `Not enough information`.

## Blocked Fields

- `games_missed_while_rostered` remains `Not enough information`.
- Identity recommendations remain proposals only and are not approved joins.
- Schedule next-game, opponent, bye, health, or availability inference remains
  gated outside this lane.

## Blocked Uses

This lane does not add:

- injury-risk score
- medical projection
- ACL/comeback projection
- durability score
- hidden sort
- model input
- rank logic
- source-truth promotion
- recommendation logic
- trade value
- pick value

## Source Rules

Player Compare consumes tracked repo artifacts only. It does not read raw
`C:\NWR_SHARED_DATA` NFLVerse files for this display.

`ff_rankings` remains blocked and unused.

## Protected Outputs

No model, rank, tier, source-truth, Outcome probability, latest approved, pinned
snapshot, trade value, pick value, or recommendation artifact is changed.
