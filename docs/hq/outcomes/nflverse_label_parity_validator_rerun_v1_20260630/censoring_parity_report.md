# Censoring Parity Report

## Result

`CENSORING_PRESERVED_NO_INCOMPLETE_WINDOW_OBSERVED_HIT_MISS`

The admitted label source preserves censoring and missingness:

- Incomplete horizon windows are marked with `window_complete=false` and retain `Not enough information` or source censoring status.
- No incomplete horizon window is treated as an observed hit or observed miss.
- Direct same-season matched rows in `matched_sidecar_label_rows.csv` use `season_outcome` labels with `censoring_status=complete_factual_season`.

## Why parity remains partial

Censoring is handled, but scoring parity remains partial because the sidecar is first-down component evidence only.
