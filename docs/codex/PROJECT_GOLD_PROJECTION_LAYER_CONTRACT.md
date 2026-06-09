# Project Gold Projection Layer Contract

This contract keeps projection inputs from becoming fake evidence during Project Gold.

## Source Statuses

| status | meaning | model treatment |
|---|---|---|
| `independent_projection` | A real imported projection source or export that independently projects future stats. | Can fill `expected_lve_points_score` and contribute normal projection confidence. |
| `local_baseline_projection` | A local baseline derived from recent imported stats, not a true forecast. | Must neutralize direct expected projection to 50, stay visible in receipts, and retain a confidence penalty. |
| `missing_projection` | No projection row exists for the player. | Projection features are neutral/imputed and source coverage remains review-needed. |
| `disabled_projection` | Projection input intentionally disabled for this player/source. | Projection features are neutral/imputed and cannot count as imported evidence. |

## Active Guardrail

Local baseline projections may still provide a transparent composite context, but they are not independent forecasts. They cannot fill `expected_lve_points_score`, cannot boost projection confidence, and must show `local_baseline_projection_not_independent` in receipts/warnings.

## Future Import Schema

A paid or independent free projection import should map to this stable shape before scoring:

| field | purpose |
|---|---|
| `player_id` | local stable player key when available |
| `source_player_id` | provider player identifier |
| `source_name` / `source_id` | provider name or local source key |
| `source_date` / `source_updated_at` | freshness date |
| `games`, `starts` | projected availability and starter role |
| `passing_yards`, `passing_tds`, `interceptions` | QB passing projection inputs |
| `rushing_attempts`, `rushing_yards`, `rushing_tds` | rushing projection inputs |
| `targets`, `receptions`, `receiving_yards`, `receiving_tds` | receiving projection inputs |
| `rushing_first_downs`, `receiving_first_downs` | direct first-down fields when available |
| `first_down_estimation_method` | direct, direct_partial, estimated, or unavailable |
| `projected_lve_points` | provider or locally rescored LVE projection |
| `confidence` | source/import confidence, only honored for independent projection rows |
| `projection_source_status` | one of the four statuses above |

## Audit Rule

Any projection feature with source status other than `independent_projection` is review evidence, not a positive model source. It should remain inspectable, lower confidence, and keep rankings review-only until accepted by gate policy.
