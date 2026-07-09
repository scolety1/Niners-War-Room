# PFR RB Broken Tackle Formula Family Note

## Future Review-Only Family

`RB Broken Tackle Context Family`

This family is a possible future review-only Formula Gauntlet slice. It is not approved for execution by this addendum.

## Allowed Hypothesis

RBs with source-season PFR rushing broken tackles may have a small contact-survival or tackle-breaking context signal after controlling for rushing volume, prior production, and PFR coverage. Prior evidence shows only tiny full-control lift, so this must be treated as weak context rather than a standalone candidate.

## Potential Future Candidates

Only after Data Hygiene and Master HQ clearance:

- `PYF + small raw broken tackle adjustment`
- `PYF + small per-game broken tackle adjustment`
- `multi_year_production + small raw broken tackle adjustment`
- `multi_year_production + small per-game broken tackle adjustment`
- `RB low-games guard + broken tackle context`
- `RB decline-risk guard + broken tackle context`

## Required Tests Before Any Advancement

- Compare against PYF.
- Control for rushing attempts/carries and prior fantasy production.
- Control for PFR coverage/missingness.
- Use source season N to target season N+1.
- Exclude blocked/collision identity rows.
- Report outlier influence.
- Report matched cohorts.
- Report holdout direction and leave-one-season-out stability.
- Report low-games harm and sparse-history harm.
- Report prior-production decline false positives.

## Blocked Uses

- No production model use.
- No rankings integration.
- No source-truth promotion.
- No PFF Elusive Rating.
- No `nwr_elusive_proxy_review_only`.
- No broad PFR feature family promotion.
- No QB/WR/TE PFR feature expansion from this addendum.

## System Audit Impact

This note does not change the Full System Audit conclusion. Formula Gauntlet remains limited to review-only component signal tests after a separate Master HQ execution contract.
