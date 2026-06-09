# Truth Set Lab v1 Import Eligibility

Status: preview/audit only. No model formulas or scores changed.

## Files

- Eligibility CSV: `local_exports\truth_set_lab\v1\reports\truth_set_import_eligibility.csv`
- Inputs reviewed: six Truth Set Lab v1 source intakes and flags

## Classification Counts

| classification | field groups |
|---|---:|
| safe_to_import | 1 |
| safe_after_derivation | 2 |
| review_only | 6 |
| rejected | 3 |

## Source Coverage

| source | field groups classified |
|---|---:|
| injury | 2 |
| trade_liquidity | 2 |
| role_usage | 2 |
| projections | 3 |
| production | 1 |
| young_player_prior | 2 |

## Import Policy

- Projection stat columns are usable only after recomputing LVE points from raw projected stats.
- Supplied projection point totals are rejected because they are not LVE-safe.
- Production data is rejected until re-exported because field alignment is unsafe.
- RB workload text from role/usage is rejected as numeric evidence.
- Unsourced healthy injury rows remain weak context only and cannot boost confidence.
- Market/trade data can enter trade/liquidity surfaces only, never private/model value.
- Young-player data feeds bridge-prior preview only; it is not veteran production evidence.

## Safe Next Move

Build the projection recompute preview layer, then the young-player bridge-prior preview. Do not import production until the source is re-exported cleanly.
