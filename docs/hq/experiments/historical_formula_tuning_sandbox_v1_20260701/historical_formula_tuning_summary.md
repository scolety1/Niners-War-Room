# Historical Formula Tuning Summary

Verdict: `YELLOW_NO_TUNING_READY_CANDIDATE_REVIEW_ONLY`

Generated at: `2026-07-01T07:57:28.044834+00:00`

Branch: `work/historical-formula-tuning-sandbox-v1-20260701`

Base HEAD: `7e99865871d11890f0bfac3fd2282525f163a40d`

Current HEAD at generation: `7e99865871d11890f0bfac3fd2282525f163a40d`

## Data Coverage

- New merged Core Usage Dataset V1: 2024-2025 player-week data, review-only.
- Admitted compact Outcome V2 labels: 2012-2024, review-only.
- Local generated Backtest V1 substrate: feature seasons 2018-2024, target seasons 2019-2025, evaluation years 2021-2025.
- Core Usage Dataset V1 alone is too shallow for a clean season N to N+1 test because admitted 2025 labels are unavailable.

## Baseline

Frozen comparison baseline: local generated `v1_baseline` predictions from Backtest V1.

- Validation ALL MAE: `35.622`
- Validation ALL Spearman: `0.704`
- Validation ALL Top-N hit: `0.576`
- Holdout ALL MAE: `32.925`
- Holdout ALL Spearman: `0.731`
- Holdout ALL Top-N hit: `0.563`

## Best Candidate By Validation MAE

Candidate: `prior_ppg_times_games_sqrt`

- Validation MAE improvement: `0.086`
- Validation Spearman improvement: `0.004`
- Validation Top-N improvement: `0.007`
- Holdout MAE improvement: `0.281`
- Holdout Spearman improvement: `-0.003`
- Holdout Top-N improvement: `-0.051`

## Recommendation

No candidate is tuning-ready. `prior_ppg_times_games_sqrt` is worth future human review only as a conservative point-error hypothesis, not as a ranking, hidden-sort, recommendation, or production formula candidate. Stable validation plus holdout Top-N/rank lift was not demonstrated.

Stable candidate IDs across validation and holdout gates: None. The best validation candidate improved point error but did not hold Top-N/rank stability.
