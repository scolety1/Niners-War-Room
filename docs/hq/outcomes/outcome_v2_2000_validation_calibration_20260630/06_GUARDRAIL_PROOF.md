# Outcome V2 2000-2024 Validation/Calibration Gate - Guardrail Proof

## Work Performed

This lane ran a review-only historical validation/calibration gate against
2000-2024 exact-scoring Outcome V2 labels.

Generated validation artifacts were written only under:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe\`

Tracked repo changes are limited to documentation and a sanitized decision
table under:

`docs/hq/outcomes/outcome_v2_2000_validation_calibration_20260630\`

## Protected Artifact Status

This lane did not modify:

- Frozen Final Draft Board V1.
- `final_board_rank`.
- Dynasty Rank.
- Tier assignments.
- Pinned snapshot/hash.
- `latest_candidate`.
- `latest_approved`.
- Production model/rank/source-truth logic.
- Rankings app wiring.
- Outcome Lens app wiring.
- Current-player probability artifacts.
- Rookie/prospect probability artifacts.
- Mock Draft, Live Draft, Deployment, Trading Lab, or runtime state.

## Source/Input Guardrails

This lane did not use or promote:

- CFBD inputs.
- DynastyProcess/market/ADP inputs.
- Gmail or vendor data.
- RotoWire/FantasyPros/FootballDB data.
- Analyst ranks.
- Projections.
- Proxy fields as model truth.
- `model_v4` generated outputs.

The source family remains public factual nflreadpy/nflverse player stats, used
only for historical review-only label validation.

## Missing Data Guardrail

Missing/censored labels remain `Not enough information`.

This lane did not treat missing values as:

- `0`
- `false`
- misses
- healthy
- low risk
- clean data

## No Tracked Local/Secret Data

This lane must not track:

- `C:\NWR_SHARED_DATA`
- `C:\NWR_LOCAL_SECRETS`
- `local_exports`
- raw cache/API/vendor/Gmail files
- runtime JSON
- secrets/API keys

The validation CSVs under `C:\NWR_SHARED_DATA` are generated local artifacts and
are intentionally untracked.

## Current Activation Status

No current-player activation is approved here.

`APPROVE_REVIEW_ONLY` means the historical label field passed this historical
validation/calibration gate. It does not mean:

- display in the live app,
- ranking integration,
- model input approval,
- hidden sort approval,
- source-truth promotion,
- protected artifact mutation,
- or current-player probability release.

## Recommended Next Lane

Run an Outcome V2 current-player activation review only if needed, and keep it
separate from this historical validation gate. That lane should explicitly
check current-player feature freshness, identity bridge status, no-leakage,
blocked source inputs, and UI/display constraints before any current-facing
artifact is considered.
