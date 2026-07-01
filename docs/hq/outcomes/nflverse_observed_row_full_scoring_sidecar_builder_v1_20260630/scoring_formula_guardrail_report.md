# Scoring Formula Guardrail Report

## Formula source

This sidecar follows the Outcome Full Scoring Formula Alignment V1 packet and the NWR scoring config `nwr_1qb_nonppr_fd_v1`.

## Guardrails

- No `fantasy_points` or `fantasy_points_ppr` fields used.
- No EPA/CPOE/share-style fields used.
- No quarantined fields used.
- No model/rank/source-truth fields used.
- `special_teams_tds` counted once only.
- Missing player-week rows remain `Not enough information`.

## Approval flags

Every emitted row has:

- `sidecar_review_allowed=true`
- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
