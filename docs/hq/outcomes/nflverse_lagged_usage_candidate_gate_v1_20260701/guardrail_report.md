# Guardrail Report

This packet is review-only.

Required false approvals:

- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `rank_logic_allowed=false`
- `app_behavior_changed=false`
- `hidden_sort_allowed=false`
- `probability_output_allowed=false`

Additional guardrails:

- Missing values are not zero unless source semantics prove explicit zero.
- Routes/TPRR/YPRR do not block the main phase.
- Do not create fake route proxies from participation data.
- Direct return touchdown subtype does not block the phase.
- `special_teams_tds` is not a return touchdown substitute.
- Plain-language audit rule: special_teams_tds is not a return touchdown substitute.
- Red-zone is source-admit / coverage-audit pending, not categorically unavailable.
- Vendor/rank/projection/market fields remain blocked as source truth.
- No app, rank, recommendation, hidden sort, model, training, or source-truth behavior is changed.
