# Rookie current-season projection model report

Selected model: `NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1`.

For each QB/RB/WR/TE rookie, the model takes the median of every granular
rookie-year stat component among earlier drafted players at the same position
and draft round. A position-only fallback is allowed only when fewer than eight
earlier same-round rows exist. All drafted players with exact identity remain in
historical outcomes; absence of a REG stat row is explicitly zero.

The 2016-2025 validation is strict walk-forward by draft class. The target class
and every future
class are absent from training. The baseline is a position-only component median.

| Position | Rows | Model MAE | Baseline MAE | Lift | Spearman |
|---|---:|---:|---:|---:|---:|
| QB | 119 | 41.6453 | 65.7144 | 24.0691 | 0.5466 |
| RB | 215 | 42.5874 | 53.8427 | 11.2553 | 0.5457 |
| TE | 141 | 25.8482 | 31.6851 | 5.8369 | 0.5115 |
| WR | 321 | 33.1495 | 44.3524 | 11.2029 | 0.5812 |

No dynasty rank, Unified Preview score, market rank, proprietary projection,
current camp depth chart, narrative role inference, or post-2025 NFL outcome
is a model input. Current 2026 facts are limited to exact identity, draft
capital, registry position, team, and ACT/RES status.

Limitations: draft capital is the only workload proxy; no 2026 depth-chart
snapshot was available; all same position/round players receive the same central
stat line; uncertainty is wide and derived from position-specific walk-forward
absolute-error p80. This is intentionally simple and auditable.
