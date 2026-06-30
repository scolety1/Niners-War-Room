# NFLVerse Approved Identity Overlay Guardrail Report

Verdict: GREEN_REVIEW_ONLY_IDENTITY_OVERLAY_READY

## Validation Summary

- Approved overlay rows: 43
- Non-approved rows: 11
- Approved rows with missing candidate NFLVerse ID: 0
- Approved rows with missing candidate GSIS ID: 0
- Approved rows with `team=needs_data`: 0
- Approved rows with `model_use_allowed=true`: 0
- Approved rows with `training_allowed=true`: 0
- Approved rows with `source_truth_allowed=true`: 0
- Approved rows with `rank_logic_allowed=true`: 0
- Approved rows with `hidden_sort_allowed=true`: 0
- Approved rows with `trade_value_allowed=true`: 0
- Approved rows with `pick_value_allowed=true`: 0

## Human Approval Boundary

Only `RECOMMEND_APPROVE_REVIEW_ONLY` rows with required NFLVerse/GSIS candidate IDs were approved. `RECOMMEND_HUMAN_REVIEW` and `RECOMMEND_KEEP_BLOCKED` rows remain out of the approved overlay.

## Repository Guardrails

No app pages, model/rank/source-truth files, latest pointers, frozen board, protected artifacts, runtime JSON, raw/shared/local/secrets, or `ff_rankings` files are changed.
