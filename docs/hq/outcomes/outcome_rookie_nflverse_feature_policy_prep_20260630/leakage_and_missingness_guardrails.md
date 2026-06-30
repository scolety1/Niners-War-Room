# Leakage And Missingness Guardrails

## Global Rule

Missing values remain:

`Not enough information`

They are never zero, false, healthy, clean, no-role, no-usage, low-risk,
confirmed UDFA, or a negative outcome.

## Identity Binding

Rows are safe for display/review only when the tracked artifact says:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`

The rebuilt artifact has `281` such rows and `13` remaining gated rows. The 13
gated rows must not expose context as truth.

## As-Of And Replay

Any future model or training feature must declare:

- prediction anchor;
- feature as-of date;
- season/week window;
- whether the source was available at the prediction time.

Future NFL production, snaps, depth chart information, roster movement, games,
awards, or career length cannot be used as pre-draft feature evidence.

## Injury And Practice

Injury report and practice status are review-only caveats. Missing injury
context is not clean health. These fields cannot create injury risk, medical
risk, recovery projection, comeback probability, or health discount.

## Schedule

Schedule next game/opponent/bye context is display-only. It cannot become a
schedule-strength model input without an explicit leakage/as-of gate.

## Depth Chart

Depth chart context is not a pre-draft feature and is not UDFA proof. It can be
current review/watchlist context only until a historical replay and leakage gate
proves safe model use.

## Snap Recency / Last Active

Snap and activity context are factual review context. Missing values do not mean
zero snaps or no activity. Model use requires anchor-aligned historical replay.

## Draft Capital / UDFA

Positive draft-pick evidence can support drafted-only review admission. Draft
absence cannot confirm UDFA. Missing draft capital remains
`Not enough information`.

## Games Missed While Rostered

`games_missed_while_rostered` remains `Not enough information` in the current
policy packet. Do not infer missed games from roster, injury, or missing stat
rows without an explicit factual denominator definition.
