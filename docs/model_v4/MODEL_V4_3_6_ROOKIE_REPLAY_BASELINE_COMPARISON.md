# Model v4.3.6 Rookie Replay Baseline Comparison

## Scope

Primary analysis uses mature 2021-2023 rows only where `Fantasy-Relevant Replay Pool == True` and outcome maturity is `three_year_window_available`.

No formula weights were changed.

## Dataset

- Mature fantasy-relevant rows: 128
- Baselines: current model, draft capital only, production/team-share only, simple hybrid capital plus production

## Verdict

Current model is worse than draft capital only in aggregate Top 20 replay.

## Aggregate Summary

| Baseline | Window | Broad Hit Rate | Strict Starter Hit Rate | Difference Makers |
|---|---|---:|---:|---:|
| current_model_score | Top 5 | 0.8 | 0.533 | 7 |
| current_model_score | Top 10 | 0.733 | 0.367 | 10 |
| current_model_score | Top 20 | 0.567 | 0.317 | 14 |
| draft_capital_only | Top 5 | 1.0 | 0.667 | 7 |
| draft_capital_only | Top 10 | 0.9 | 0.5 | 10 |
| draft_capital_only | Top 20 | 0.7 | 0.35 | 14 |
| production_team_share_only | Top 5 | 0.6 | 0.4 | 3 |
| production_team_share_only | Top 10 | 0.6 | 0.433 | 10 |
| production_team_share_only | Top 20 | 0.583 | 0.317 | 14 |
| simple_hybrid_capital_plus_production | Top 5 | 0.867 | 0.467 | 4 |
| simple_hybrid_capital_plus_production | Top 10 | 0.833 | 0.433 | 9 |
| simple_hybrid_capital_plus_production | Top 20 | 0.667 | 0.367 | 15 |

## By-Position Notes

| Baseline | Position | Window | Broad Hit Rate | Strict Starter Hit Rate |
|---|---|---|---:|---:|
| current_model_score | QB | Top 20 | 1.0 | 0.75 |
| current_model_score | RB | Top 20 | 0.571 | 0.429 |
| current_model_score | WR | Top 20 | 0.514 | 0.2 |
| draft_capital_only | QB | Top 20 | 1.0 | 0.7 |
| draft_capital_only | RB | Top 20 | 0.889 | 0.667 |
| draft_capital_only | TE | Top 20 | 0.6 | 0.2 |
| draft_capital_only | WR | Top 20 | 0.581 | 0.194 |
| production_team_share_only | QB | Top 20 | 0.889 | 0.556 |
| production_team_share_only | RB | Top 20 | 0.625 | 0.5 |
| production_team_share_only | TE | Top 20 | 0.571 | 0.143 |
| production_team_share_only | WR | Top 20 | 0.464 | 0.179 |
| simple_hybrid_capital_plus_production | QB | Top 20 | 0.909 | 0.636 |
| simple_hybrid_capital_plus_production | RB | Top 20 | 0.818 | 0.636 |
| simple_hybrid_capital_plus_production | TE | Top 20 | 0.571 | 0.286 |
| simple_hybrid_capital_plus_production | WR | Top 20 | 0.548 | 0.194 |

## Guardrails

- This is a replay evaluation layer, not formula tuning.
- Market-only baseline is future work and is not used for private value.
- No active rankings, My Team, War Board, readiness gates, or app promotion changed.
