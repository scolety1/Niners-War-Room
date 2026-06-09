# Feature Data Truth Contract

Project Gold Sprint 1 Phase 2 freezes model math and makes input provenance explicit.
The model must distinguish real evidence from derived evidence, neutral defaults, manual-review evidence, and disabled features.

## Status Categories

| status | meaning |
|---|---|
| `imported_real_data` | Direct imported source field exists and is usable. |
| `derived_real_data` | Formula/proxy derived from imported source fields. |
| `neutral_imputation` | Missing source was replaced by a neutral/default value. |
| `manual_review` | Value may be useful, but source is stale, proxy-only, or locally estimated. |
| `disabled` | Feature is intentionally inactive for this player/context. |

## Active Feature Coverage

The implementation contract lives in `src/services/feature_data_truth_contract_service.py`.
It covers the active stats-first features:

- `weighted_recent_lve_ppg_score`
- `expected_lve_points_score`
- `lve_projection_value`
- `role_security`
- `workload_earning`
- `target_earning_stability`
- `route_role`
- `efficiency_score`
- `first_down_td_fit`
- `age_curve`
- `injury_durability`
- `private_stat_value`
- `confidence` / `confidence_score`
- `market_liquidity` / `market_trade_value`
- `young_nfl_bridge_prior`

## Known Defaults

| default | contract meaning |
|---:|---|
| `50` | Neutral midpoint for missing production, projection, role, efficiency, first-down/TD, age, replacement fallback, or market fallback. |
| `75` | Normalization injury fallback when injury source rows are missing. |
| `76` | Formula-level injury fallback and QB replacement fallback. |
| `78` | Formula-level RB/WR/TE injury fallback in selected subformulas. |

These defaults may be useful as safety rails, but they are not imported player evidence.
