# Gate D Feature Policy Decision - 2026-06-30

## Verdict

`PARTIAL_FEATURES_ALLOWED_FOR_REVIEW_ONLY_MODEL_RD`

Enough non-leaky factual features exist for a limited Gate E review-only R&D lane: position, draft year / rookie class year, draft round, draft pick, and derived draft-capital buckets.

## Allowed For Future Review-Only Model R&D

- `position`
- `draft_year`
- `rookie_class_year`
- `draft_round`
- `draft_pick`
- `draft_capital_bucket` if derived from round/pick and documented in Gate E

All remain:

- `review_only=true`
- `model_use_allowed=false`
- `training_allowed=false`

## Review-Only Context Only

- drafted team / initial NFL landing spot
- college team
- GSIS/player_stats/NWR/CFBD IDs as join keys
- CFBD identity and production context
- size / height / weight
- age if later extracted into an approved bridge

## Blocked Or Missing

- CFBD production-derived features until source/human approval
- recruiting, combine/pro day, early declare, transfer timeline, market share/dominator
- UDFA/free-agent rookie entry context
- market, ADP, DynastyProcess
- vendor/Gmail/FantasyPros/RotoWire/news
- projections and medical/injury projection

## Leakage Rules

Historical rookie outcome labels may be review targets only. Rookie-year, year-2, first-3-year, and first-5-year NFL production/labels must never be input features.

## Gate E

Gate E can run next as a limited review-only model R&D / feasibility lane. It must not create production probabilities, Rankings wiring, model-use rows, training-use rows, or source-truth promotion.
