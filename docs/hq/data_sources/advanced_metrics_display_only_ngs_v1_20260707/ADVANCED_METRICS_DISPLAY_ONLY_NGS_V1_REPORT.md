# Advanced Metrics Display-Only NGS V1 Report

Verdict: `YELLOW_DISPLAY_ONLY_NGS_DOCS_ONLY`

This lane prepares a safe display-only contract for public NGS metrics. It does not implement runtime UI. It does not change rankings, formulas, default sorting, hidden sorting, model inputs, recommendations, trade logic, draft logic, or source truth.

## Baseline

- Source branch: `work/lane-advanced-metrics-hardening-v2-backtest-20260707`
- Source commit: `3e28a357f47ef55e54746306ead5c9fbe38baa56`
- V2 packet found and tracked: `docs/hq/data_sources/advanced_metrics_hardening_v2_backtest_20260707/`
- V2 verdict: `YELLOW_ADVANCED_METRICS_V2_BACKTEST_MIXED`

## Decision

NGS is appropriate as a display-only/review-only candidate for Development Lab, Player Compare, and Data Health. Runtime implementation is deferred to a separate lane because the display contract should be reviewed before app surfaces are touched.

NGS remains not approved for production model/rank usage. V2 backtest evidence was mixed: QB declined, RB was near flat, WR/TE showed small review-only lift.

## Allowed Display Families

- QB: CPOE, expected completion percentage, average time to throw, aggressiveness, air yards to sticks, intended air yards, completed air yards.
- RB: rush yards over expected, RYOE per attempt, rush percentage over expected, rushing efficiency, 8+ box rate, time to line of scrimmage.
- WR/TE: average separation, cushion, expected YAC, YAC over expected, share of intended air yards, average intended air yards.

## Guardrails

Every display must say `Review-only NGS context`. Public NGS thresholding can hide low-volume players, so missingness must be visible and never treated as zero. NGS must not produce a score, grade, recommendation, verdict, boost, sort, or rank.
