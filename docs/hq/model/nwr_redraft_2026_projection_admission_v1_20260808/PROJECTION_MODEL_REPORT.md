# Projection model report

Selected model: `NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1`.

The central forecast copies each exact current veteran's 2025 granular stat line into a 2026
forecast, updates identity/team/status from the July 30 current registry, and attaches historical
position-specific uncertainty. It is intentionally conservative and separate from all dynasty
rankings. Players without a 2025 line and every 2026 rookie are blocked.

The first recency/per-game/regression formulation was rejected because its 2016-2025 temporal MAE
was worse than prior-season persistence in every position. No tuning was used to conceal that
result. The selected persistence baseline materially beats a position-median baseline in every
backtest season and retains useful rank correlation.

2024-2025 mean validation:

```
position  model_mae  spearman
      QB    58.5312    0.6886
      RB    36.1442    0.7470
      TE    22.9600    0.7390
      WR    32.5122    0.7644
```

Limitations are material: no explicit 2026 workload, coaching, scheme, or injury adjustment; no
rookie workload; no K/DST; and no role-growth/decline forecast. The NWR Owner accepted those
limitations for the exact SHA-bound veteran-only Redraft scope on 2026-08-08. They remain disclosed
and do not authorize use outside Redraft V1.
