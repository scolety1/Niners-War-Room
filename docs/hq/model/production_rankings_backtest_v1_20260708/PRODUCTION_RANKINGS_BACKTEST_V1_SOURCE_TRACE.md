# Production Rankings Backtest V1 Source Trace

## Production Surface

- Active route/page: `app/pages/20_final_board_v1.py`.
- Loader: `load_dynasty_rankings()` in `src/services/draft_day_app_v1_service.py`.
- Current artifact file name: `full_player_board_value_review_rows.csv`.
- Primary rank field: `nwr_rank`.
- Primary score field: `nwr_dynasty_score`.
- Rank assignment: `_assign_private_ranks()` in `src/services/full_player_board_value_service.py` sorts scored rows descending by `nwr_dynasty_score`; league and market ranks only affect display/fallback ordering for unscored rows.

## Source Files

| Path | Exists | SHA-256 | Role |
| --- | --- | --- | --- |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\app\pages\20_final_board_v1.py | True | 03f434a269241046828199b99e73c8057c272ffb5e45afc92637630a30796aed | Code trace / formula or loader behavior. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\src\services\draft_day_app_v1_service.py | True | a16035363e4aa13f9f5f37c6ed58143fdf9703590192cde79ceefccccd0289dc | Code trace / formula or loader behavior. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\src\services\full_player_board_value_service.py | True | ddd88c8d8b382a63fe593a89122d0ba55859fa4d582b41529e18147b80688731 | Code trace / formula or loader behavior. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\src\services\model_v4_formula_contract_service.py | True | a379ba19661c2619d875b8d645c236f60e632c67016d56ab3ee13dca39a8b564 | Code trace / formula or loader behavior. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\config\nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json | True | 03986944a57f0f73c78a8f56413b53749b3e384a10788ff7ab262d21e0b1eab2 | League/scoring contract. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\config\source_registry.csv | True | aa44797ddca17c1aa9133fea6a47716087652c07dde9874c44a59983bb223d48 | Local review-safe evidence or baseline metrics. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701\nwr_historical_tuning_feature_target_substrate_v3.parquet | True | 6b80a71af609932c91553413319902d2a61a4b24c36060d3c724747672f9797a | Historical feature-target substrate. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701\safe_feature_allowlist_v3.csv | True | 520866fc86ee356bbf000ab33861fdd92ae45b8728f9a51d6ea0334e6a30304a | Local review-safe evidence or baseline metrics. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701\historical_tuning_substrate_v3_summary.md | True | d49d9ae11f2be0297ea60dd1b86681b7d1cc0ae259caa1bba3a0cb2d7057db1c | Governance, source, or leakage decision record. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701\asof_and_leakage_guardrail_report_v3.md | True | 19caca810f352a6f5222f97f1ffa2ece5b9ef21969ed98e6461a57dcfbc45349 | Governance, source, or leakage decision record. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701\identity_join_report_v3.csv | True | d21ad2346acb8505a02e251d68d37f44be5fa4026300df4968a9bb4fefcb20a5 | Local review-safe evidence or baseline metrics. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_tuning_source_contract_v1_20260701\formula_tuning_not_ready_reason.md | True | 22eedbda00aeb088ec8df593f08159580a5ff4c9fbedd79db9ff66f45c40bca9 | Governance, source, or leakage decision record. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_formula_tuning_sandbox_v1_20260701\baseline_accuracy_report.csv | True | bb7b9a475a08fa17b723719a6c88ca3ccd607875aa777c40cb92eec682d9a728 | Local review-safe evidence or baseline metrics. |
| C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708\docs\hq\experiments\historical_formula_candidate_search_v1_20260701\validation_leaderboard.csv | True | 415697cf3659120fb19f1fffdd50857089a834ff347cf44476f230edde0a7672 | Local review-safe evidence or baseline metrics. |
| C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv | True | 263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4 | Pinned current full dynasty ranking artifact read-only. |

## Current Board Facts

- Current board rows: `240`.
- Current scored rows: `232`.
- Current board hash matches app-pinned hash: `True`.
- Current board positions: `{'WR': 93, 'RB': 79, 'TE': 32, 'QB': 28, 'K': 8}`.

## Historical Substrate Facts

- Rows: `5518`.
- Positions: `{'WR': 2124, 'RB': 1429, 'TE': 1211, 'QB': 754}`.
- Feature seasons: `2012-2024`.
- Target seasons: `2013-2025`.
- All rows review-only: `True`.
- Any model-use-allowed rows: `False`.
- Any production-approved rows: `False`.
