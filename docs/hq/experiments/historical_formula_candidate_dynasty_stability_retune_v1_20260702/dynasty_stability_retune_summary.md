# Historical Formula Candidate Dynasty Stability Retune V1

Verdict: `YELLOW_PARTIAL_DYNASTY_STABILITY_RETUNE_STILL_HOLD_REVIEW_ONLY`

Decision label: `PARTIAL_DYNASTY_STABILITY_RETUNE_STILL_HOLD`

Selected review-only retune: `multi_year_plus_cornerstone_guard`

This packet is a bounded review-only retune evaluation. It does not change production formulas, rankings, app behavior, model behavior, source truth, hidden sort, recommendations, runtime logic, or production config.

## Historical Summary

- Validation MAE delta vs baseline: `-0.840566`
- Validation Spearman delta vs baseline: `0.009381`
- Validation startable precision delta vs baseline: `-0.005952`
- Holdout MAE delta vs baseline: `-1.308282`
- Holdout Spearman delta vs baseline: `0.015626`
- Holdout startable precision delta vs baseline: `0.0`
- Holdout MAE delta vs current guarded candidate: `-0.111899`
- Holdout position harm count: `1`
- Holdout season harm count: `0`

## Current Board Summary

- Current-board rows: `370`
- Candidate-ready rows: `245`
- Null-fenced rows: `125`
- Players changed by retune preview: `10`
- Key audit players improved or reduced: `8`

No candidate is production-approved.

## Validation Completion

- Project-approved test runner: `C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- Focused artifact/schema test: `4 passed`
- Relevant candidate/source/substrate/governance/scoring suite: `82 passed`
- Default Python pytest gap is resolved by the project-approved runner. No focused tests were skipped in the completed runner pass.

## Final Decision Clarification

- Candidate remains `HOLD`.
- Production promotion is not approved.
- Main-formula readiness is not approved.
- Retune evidence is useful because it reduces current-board cornerstone underrank risk while preserving holdout MAE/Spearman gains.
- Malik Nabers should be treated as `INJURY_TIMELINE_DISCOUNT_WATCHLIST`, not an automatic dynasty-stability failure.
- Garrett Wilson should be treated as `EXPLAINABLE_WATCHLIST`, not an automatic formula failure.
- CeeDee Lamb, Justin Jefferson, and Brock Bowers still deserve stronger dynasty-stability protection if the formula is too low.
- DeVonta Smith and Jaylen Waddle role-up context remains important review evidence.
- Treat the candidate as a usage/stability lens unless a future targeted proven-cornerstone fix clears those cases without blindly boosting market-favored names.
