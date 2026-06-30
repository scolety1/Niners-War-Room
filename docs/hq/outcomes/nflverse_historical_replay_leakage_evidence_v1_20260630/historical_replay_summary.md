# Historical Replay Summary

Verdict: `YELLOW_HISTORICAL_REPLAY_LEAKAGE_EVIDENCE_READY`

This lane converts the Outcome/Rookie NFLVerse Feature Policy Gate V1 into a replay-risk audit. It defines the evidence required before any NFLVerse display/review field could be considered for a later sandbox or shadow experiment.

## Executive Decision

No feature family is safe for model experiment now.

Current display safety does not imply model safety. The current NFLVerse player-context artifact is built for display/review context on the current player universe. It is not a point-in-time historical feature panel.

## Current Display Facts Preserved

- NFLVerse display/update wave verdict: `GREEN_DISPLAY_UPDATE_COMPLETE_WITH_13_IDENTITY_ROWS_GATED`.
- Player context artifact rows: `294`.
- Safe display rows: `281`.
- Remaining gated rows: `13`.
- Newly activated bound rows from rebuild: `41`.
- NFLVerse remains display/review-only.
- Missing values stay `Not enough information`.

## Feature Risk Summary

Rows audited in `historical_replay_feature_matrix.csv`: `19`.

- Safe for current display now: `12` families, only within existing display/review guardrails.
- Safe for historical replay now: `0` families.
- Safe for model experiment now: `0` families.
- Families needing point-in-time snapshots before replay: `14`.
- Families blocked by source policy or guardrail policy: `5`.
- Families not model eligible or prerequisite-only: `2`.

## Main Leakage Findings

Current roster, weekly roster, injury, practice, depth chart, snap, last active, schedule, and availability fields carry high leakage risk unless each row can prove prediction-time availability from a historical snapshot.

Post-draft fields such as draft capital and combine measurements may be future candidates only under the correct prediction anchor. They are not pre-draft rookie features unless the feature was known at the selected pre-draft anchor, and draft capital is post-draft-only.

Player stats sidecars are not input features. They require label parity or sidecar comparison gates and cannot become label truth, source truth, model input, or training truth here.

Contract context remains non-model-eligible. Identity bridge health remains a prerequisite guardrail, not a predictive model feature.

CFBD joins, UDFA status, `ff_rankings`, and market / ADP / DynastyProcess remain blocked. Draft absence, roster appearance, snap appearance, player_stats appearance, depth-chart appearance, injury context, and schedule context cannot confirm UDFA status.

## Approval Status

- `allowed_for_model_now=false` everywhere.
- `allowed_for_training_now=false` everywhere.
- `allowed_for_source_truth_now=false` everywhere.
- `safe_for_model_experiment_now=false` everywhere.

No model training, tuning, probability generation, app wiring, rank logic, hidden sort, source-truth promotion, recommendation logic, trade value, or pick value changed.
