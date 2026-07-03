# Usage/Stability Lens Development Lab Parking

Verdict: `GREEN_DEV_LAB_USAGE_STABILITY_LENS_PARKED_REVIEW_ONLY`

The Usage/Stability Lens is parked in Development Lab as a dormant review-only experiment. It is not a ranking system and does not affect the main board.

## Current Status

- Candidate status: `HOLD`
- Interpretation: `REVIEW_ONLY_USAGE_STABILITY_LENS`
- Production promotion: not approved
- Main-formula readiness: not approved
- App/live preview: not approved
- Rankings behavior: unchanged
- Hidden sort/recommendations: not approved
- Source-truth promotion: not approved

## Development Lab Display Scope

Development Lab may show only static review metadata:

- warmer rows: `115`
- colder rows: `127`
- null-fenced rows: `125`
- example: CeeDee Lamb is `LENS_COLDER_THAN_BASELINE`
- example note: "Lens is colder: player moved from WR11 to WR18."

The static label-fixed packet path may be displayed as a manual path only:

`C:\NWR_REVIEW\static_human_review_usage_stability_lens_packet_v1_20260703_label_fix\index.html`

The app must not open, regenerate, score, or require that outside-repo packet. Missing packet context is not an app failure.

## Guardrails Preserved

- No production formula changes.
- No production model training or tuning.
- No production config changes.
- No rankings/default behavior changes.
- No source-truth promotion.
- No hidden sort or recommendations.
- No broad tuning.
- No market/ADP/vendor/projection/rank fields as source truth.
- No routes, TPRR, YPRR, ambiguous `rz_att`, unsafe red-zone sidecar, or unsafe current-only context.
- Missing values remain null / `Not enough information`.
