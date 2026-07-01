# Next Gate Recommendations

## Recommended Next Lane

Run a point-in-time availability denominator replay lane before any health/model/training/source-truth consideration.

## Required Evidence

1. Define exact rostered-at-game eligibility rules.
2. Define active, inactive, injured reserve, practice squad, and unavailable handling.
3. Exclude bye weeks and document postponed/canceled game handling.
4. Prove schedule, roster, snap, stat, and injury-report data were available as of the relevant historical week.
5. Preserve identity gating and exclude unresolved identity rows.
6. Keep missing data as `Not enough information`.
7. Test that missing snaps/stats/injury reports are not converted to zero, healthy, clean, low-risk, inactive, or missed.
8. Run leakage and label interaction audits before any model/training proposal.

## Current Recommendation

Use existing denominator fields only as tracked display/review context where `denominator_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`. Keep `games_missed_while_rostered` blocked.
