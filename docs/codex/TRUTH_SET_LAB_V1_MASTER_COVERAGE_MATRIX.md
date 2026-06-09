# Truth Set Lab v1 Master Coverage Matrix

Status: preview/audit only. No model scores changed.

## Files

- Matrix CSV: `local_exports\truth_set_lab\v1\reports\truth_set_master_coverage_matrix.csv`
- Source buckets: injury, trade liquidity, role/usage, projections, production, young-player prior

## Bucket Status Counts

| bucket | model_safe | preview_only | not_model_safe | missing | not_applicable |
|---|---:|---:|---:|---:|---:|
| injury | 0 | 40 | 0 | 0 | 0 |
| trade_liquidity | 0 | 5 | 0 | 35 | 0 |
| role_usage | 0 | 40 | 0 | 0 | 0 |
| projections | 0 | 38 | 0 | 2 | 0 |
| production | 0 | 0 | 40 | 0 | 0 |
| young_player_prior | 0 | 20 | 0 | 3 | 17 |

## Recommendation Counts

| bucket | can_import | can_import_after_recompute | needs_manual_review | needs_reexport | do_not_use |
|---|---:|---:|---:|---:|---:|
| injury | 7 | 0 | 33 | 0 | 0 |
| trade_liquidity | 5 | 0 | 35 | 0 | 0 |
| role_usage | 2 | 0 | 38 | 0 | 0 |
| projections | 0 | 38 | 2 | 0 | 0 |
| production | 0 | 0 | 0 | 40 | 0 |
| young_player_prior | 0 | 0 | 40 | 0 | 0 |

## Main Findings

- Production is present for all 40 players but is `not_model_safe`; it needs a corrected re-export because field alignment is unreliable.
- Projection stat rows are broadly useful only after recomputing LVE points; supplied points must not be used directly.
- Trade liquidity is available for only 5 players; missing market must not create fake edge.
- Injury has many unsourced healthy rows; use as weak preview context only.
- Role/usage is preview-only because multiple rows contain uncertainty markers or malformed source extraction, especially RB workload fields.
- Young-player prior covers 20 players; Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers are missing young-eligible controls.

## Safe Next Move

Proceed to import eligibility classification. Do not promote any source into active scoring from this matrix alone.
