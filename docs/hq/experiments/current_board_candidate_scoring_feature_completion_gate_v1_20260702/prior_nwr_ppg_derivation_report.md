# prior_nwr_ppg Derivation Report

Status: `COMPLETED_WHEN_PRIOR_GAMES_GT_0`

Formula:

`prior_nwr_ppg = prior_nwr_points / prior_games`

The calculation is performed only when `prior_games > 0`. Rows without prior factual rows remain null-fenced. No no-stat player receives `0.0` PPG.
