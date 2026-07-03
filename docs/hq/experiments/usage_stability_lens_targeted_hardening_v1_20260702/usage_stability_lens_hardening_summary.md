# Usage/Stability Lens Targeted Hardening Summary

Decision label: `KEEP_AS_USAGE_LENS_ONLY_NO_RANK_VARIANT`

Selected review posture: `usage_lens_with_cornerstone_warning_flags`

This lane reviewed six fixed hardening variants for the current usage/stability lens. The review did not run broad tuning, did not search thresholds on holdout, and did not change production formulas. The historical evidence still says the lens has useful usage/opportunity signal, but the current-board evidence does not justify rank replacement.

The strongest bounded improvement is not a new rank formula. It is a human-review warning layer that separates proven cornerstone stability concerns from explainable watchlist cases. That preserves Tim's review context: Malik Nabers and Garrett Wilson are not automatic model failures, while CeeDee Lamb, Justin Jefferson, and Brock Bowers remain stronger dynasty-stability protection cases.

## Summary Decision

- `multi_year_plus_cornerstone_guard` remains the current best historical lens evidence.
- The new hardening review does not promote it.
- The safest next state is review-only usage/stability lens plus warning flags.
- Production promotion remains `NOT_APPROVED`.
- Main-formula readiness remains `NOT_APPROVED`.
- Shadow rank replacement remains `NOT_APPROVED`.

## Why This Is Conservative

The fixed rank-changing variants preserve some historical usefulness, but each still risks overfitting or over-correcting player archetypes Tim explicitly wants reviewed rather than blindly boosted. The warning-flag variant improves the review workflow without mutating rank outputs or forcing market agreement.

## Required Follow-Up

If Tim wants more movement, the next gate should be a narrow human-review shadow lens packet, not another broad formula tuning pass.
