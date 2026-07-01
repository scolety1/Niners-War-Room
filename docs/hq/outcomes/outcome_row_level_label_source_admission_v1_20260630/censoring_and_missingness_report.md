# Censoring and Missingness Report

## Result

Censoring and missingness are preserved in the compact artifact.

## Validation performed

- Season labels are factual completed season rows and receive `window_complete=true` with `censoring_status=complete_factual_season`.
- Anchor horizon labels preserve the source window completeness fields:
  - `this_year_window_complete`
  - `next_year_window_complete`
  - `within_5y_window_complete`
- Incomplete anchor windows were checked before derivation. No incomplete window carried `hit` or `miss`; incomplete windows use `Not enough information`/source censoring status.
- `Not enough information` is preserved as `label_value=Not enough information` and `hit_status=Not enough information`.
- `not_applicable` is preserved as `hit_status=not_applicable`.

## Compact artifact counts

| Status | Rows |
| --- | ---: |
| Observed hit | 9,119 |
| Observed miss | 52,989 |
| Not applicable | 15,594 |
| Not enough information | 41,338 |
| Rows with incomplete horizon window | 49,676 |

## Guardrail

Missing or censored labels are not failures, misses, zeros, or low probabilities.
