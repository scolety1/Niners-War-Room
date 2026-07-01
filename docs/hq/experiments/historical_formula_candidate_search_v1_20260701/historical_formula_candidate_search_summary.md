# Historical Formula Candidate Search V1

Verdict: `GREEN_REVIEW_ONLY_CANDIDATE_SEARCH_COMPLETED`

Candidate verdict: `STRONG_REVIEW_ONLY_CANDIDATE_NOT_PRODUCTION_APPROVED`

This is a bounded review-only formula candidate search following the merged readiness gate decision `GO_LIMITED_FORMULA_SEARCH_REVIEW_ONLY`. It does not change production formulas, rankings, app behavior, model behavior, source truth, hidden sort, recommendations, runtime logic, or production config.

## Coverage

- Rows: `5,518`
- Feature seasons: `2012-2024`
- Target seasons: `2013-2025`
- Split rows: train `3,716`, validation `912`, holdout `890`
- Position rows: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`

## Results

- Baseline validation MAE: `34.86049`
- Baseline holdout MAE: `35.880449`
- Best validation candidate: `usage_opportunity_volume` with MAE delta `-2.0366209999999967`
- Selected candidate for one-time holdout review: `usage_opportunity_volume`
- Selected holdout MAE delta: `-1.646492000000002`
- Selected holdout Spearman delta: `0.0011259999999999604`
- Worth human review only: `True`

No candidate is production-approved.
