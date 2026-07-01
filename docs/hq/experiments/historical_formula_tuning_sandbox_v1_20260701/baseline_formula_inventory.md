# Baseline Formula Inventory

This sandbox did not alter production formulas or ranking behavior.

## Formula Config

- Source: `docs\model_v4\MODEL_V4_FORMULA_CONFIG.json`
- Formula version: `model_v4_review_only_0.2.1`
- Status: `review_only`
- Active rankings affected: `False`
- Generated rankings: `False`

## Position Component Weights

| Position | Components |
| --- | --- |
| RB | production=24; first_down_scoring_fit=14; usage_opportunity=24; snap_proxy_role=8; projection=10; age_dropoff=12; young_player_prior=8; injury_context_confidence_effect=0 |
| WR | production=22; first_down_scoring_fit=12; usage_opportunity=20; snap_proxy_role=5; projection=19; age_dropoff=12; young_player_prior=10; injury_context_confidence_effect=0 |
| QB | production=18; first_down_scoring_fit=6; usage_opportunity=10; snap_proxy_role=4; projection=10; age_dropoff=7; position_scarcity_suppression=41; young_player_prior=4; injury_context_confidence_effect=0 |
| TE | production=22; first_down_scoring_fit=10; usage_opportunity=24; snap_proxy_role=8; projection=10; age_dropoff=10; no_premium_suppression=10; young_player_prior=6; injury_context_confidence_effect=0 |

## Scoring Config

- Source: `config\nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`
- Scoring version: `nwr_1qb_nonppr_fd_v1`
- Format: 10-team 1QB non-PPR first-down scoring.
- Regular-season scoring calendar is the default scope.

## Frozen Evaluation Baseline

The quantitative baseline is the local generated Backtest V1 `v1_baseline` prediction artifact. It is not a production formula update, and it remains review-only.
