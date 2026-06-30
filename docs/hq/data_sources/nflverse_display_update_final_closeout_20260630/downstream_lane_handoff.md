# Downstream Lane Handoff

Use this handoff for future app, Outcome, Rookie, and model-policy lanes.

## Safe To Consume For Display

The rebuilt NFLVerse player context display artifact may be consumed for
display/review-only app context where all existing row and field gates pass.

Required row rules:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- schema/status gates pass
- conservative flags remain false for model, training, source truth, rank logic,
  hidden sort, trade value, and pick value

Safe row count at closeout: 281.

## Still Gated

The 13 gated rows must remain `Needs identity review` or
`Not enough information`. They must not expose player context details.

Kentrel Bullock and Jamal Haynes need future NWR/Sleeper binding review. Chip
Trayanum needs future explicit human confirmation. No current packet approves
those rows.

## Display Language

Use language such as:

- `Display-only`
- `Review-only context`
- `Not model input`
- `Not enough information`
- `Needs identity review`

Avoid language that implies:

- recommendation
- model confidence
- rank movement
- trade value
- pick value
- health/injury risk
- medical projection
- source truth

## Model And Outcome Boundary

The closeout does not approve any NFLVerse field for model input, training,
source truth, Outcome/Rookie activation, active rookie probabilities, Gate G,
UDFA modeling, CFBD model/training input, or `ff_rankings`.
