# Availability Denominator Guardrail Report

Verdict: YELLOW_PARTIAL_DENOMINATOR_ARTIFACT_READY

## Guardrail Proof

- Every row has `display_only=true`.
- Every row has `review_only=true`.
- Every row has `model_use_allowed=false`.
- Every row has `training_allowed=false`.
- Every row has `source_truth_allowed=false`.
- Every row has `rank_logic_allowed=false`.
- Every row has `hidden_sort_allowed=false`.
- Every row has `trade_value_allowed=false`.
- Every row has `pick_value_allowed=false`.
- Identity-review rows have denominator fields set to `Not enough information` and status `NEED_IDENTITY_APPROVAL`.
- Missing snap/stat/roster data is not converted to 0/false/healthy/clean/no-role.
- `games_missed_while_rostered` remains `Not enough information` for all rows.
- No raw/shared/cache/local/secret files are tracked by this packet.
- No `ff_rankings` source is used.

## Non-Use Statement

This artifact must not drive rankings, model input, source truth, hidden sort, recommendations, injury risk, medical projection, durability scoring, trade value, or pick value.
