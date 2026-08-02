# Full-Suite Baseline Comparison

| Run | Passed | Failed/errors | Skipped | Seconds |
|---|---:|---:|---:|---:|
| Prior raw diagnostic | 3195 | 273 | 71 | Not recorded |
| Canonical | 3199 | 269 | 71 | 595.79 |
| Candidate | 3214 | 269 | 71 | 573.93 |

The clean canonical reproduction reduced four failures from the prior raw diagnostic without a product-authority change. Classification counts: `{"INTENTIONALLY_BLOCKED": 71, "KNOWN_BASELINE_EXCEPTION": 90, "MISSING_IGNORED_HISTORICAL_ARTIFACT": 177, "STALE_CANONICAL_EXPECTATION": 2}`. Product defects repaired: `0`; new regressions: `0`.
