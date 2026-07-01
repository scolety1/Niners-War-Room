# Next Dataset Builder Handoff

Recommended next checkpoint: `Core Usage Review Dataset V1`.

## Builder Goal

Create a compact review-only season N to season N+1 factual usage artifact. The builder should use completed season N usage as a lagged context layer and preserve all approval flags as false.

## Required Inputs

- Sleeper/NFLVerse Usage Red-Zone Source Admission V1 packet.
- NFL Usage historical panel/review artifacts.
- NFLVerse player_stats source admission receipts.
- NFLVerse point-in-time feasibility/manifest packets.
- Identity-safe player mapping packets where applicable.

## Required Output Fields

Candidate families:

- Targets.
- Carries.
- Receptions.
- Rushing yards.
- Receiving yards.
- Air yards.
- YAC.
- First downs.
- Offense snaps.
- Snap share after denominator validation.
- Touches.
- Opportunities.
- Typed red-zone opportunities after semantics checks.

## Required Row Policy

Each row must include:

- Feature season N.
- Target season N+1.
- Prediction anchor.
- Source as-of statement.
- Source receipt path or compact receipt ID.
- Missingness status.
- Review-only flag.
- `model_use_allowed=false`.
- `training_allowed=false`.
- `source_truth_allowed=false`.
- `rank_logic_allowed=false`.
- `hidden_sort_allowed=false`.
- `recommendation_allowed=false`.

## Blocked For This Builder

- Current roster/status/availability.
- Current schedule/next game/opponent/bye.
- Injury/practice context.
- Depth chart context.
- Routes/TPRR/YPRR unless rights-cleared and already approved.
- `rz_att` until semantics are proven.

## Validation

The builder must prove:

- No target-season rows entered feature columns.
- Nulls were preserved.
- Sparse keys were not converted to zero.
- Red-zone typed fields were not collapsed into ambiguous `rz_att`.
- PBP `yardline_100 <= 20` fallback, if used, remains review-only validation/fallback.
- All approval flags remain closed.
