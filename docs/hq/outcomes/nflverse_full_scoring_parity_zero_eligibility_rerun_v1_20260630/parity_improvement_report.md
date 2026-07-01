# Parity Improvement Report

## Classification

`PARITY_IMPROVED_REVIEW_ONLY` for positions where matched player-seasons include rostered-active safe-zero weeks, but the overall lane remains partial because global parity is still blocked.

## What improved

- The parity subset admits `88` rostered-active no-stats safe-zero player-week rows.
- `23` deterministic matched 2024 player-seasons include at least one rostered-active safe-zero week.
- These rows improve review context for whether observed zero weeks can be distinguished from missing information.

## What did not improve

- Matched player-seasons decreased from `186` to `176` because the rerun only uses the approved zero-eligibility parity subset.
- Matched label rows decreased from `2,976` to `2,816`.
- No 2025 label rows exist in the admitted label source.
- Full/global scoring parity remains false.
