# Player Compare Display-Only NGS Test Report

Validation should confirm:

- Player Compare renders `Review-only NGS Context`.
- The tab labels NGS as display-only and not used in rankings.
- Side-by-side values are produced only from safe identity rows.
- Identity-review rows and missing NGS values show unavailable/thresholded rather than approved values or zero.
- Blocked metric families remain excluded.
- Existing Development Lab/Data Health NGS checks still pass.
- Rankings/default-sort checks still pass.

The final validation results are recorded in `player_compare_display_only_ngs_test_results.csv`.
