# PFR RB Broken Tackle Addendum Guardrails

## Hard Scope

- RB only.
- Review-only.
- Public nflverse PFR advanced stat parquet context only.
- Source season N to target season N+1 only.
- Safe PFR rushing bridge rows only.
- Blocked/collision rows excluded.

## Not Approved

- PFR production use.
- Broad PFR feature promotion.
- PFR QB passing model use.
- WR/TE PFR feature expansion.
- Ranking integration.
- App/runtime behavior changes.
- Source-truth promotion.
- Formula tuning.
- Formula Gauntlet execution.

## Blocked Names And Metrics

- PFF Elusive Rating.
- `nwr_elusive_proxy_review_only`.
- Any PFF-style elusive/proxy label.
- Any language implying this is equivalent to proprietary PFF charting.

## Required Future Controls

Any future Master HQ-approved component signal test must:

- Compare against PYF.
- Control for rushing volume.
- Control for prior production.
- Control for PFR coverage/missingness.
- Report outlier influence.
- Report matched cohorts.
- Report holdout direction.
- Report low-games harm.
- Report sparse-history harm.
- Treat effect as tiny/weak unless materially stronger evidence appears.

## Readiness Impact

This addendum does not loosen Formula Gauntlet readiness. The current maximum remains:

`CLEARED_FOR_REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

100-candidate Gauntlet, champion refinement, and rankings integration remain blocked.
