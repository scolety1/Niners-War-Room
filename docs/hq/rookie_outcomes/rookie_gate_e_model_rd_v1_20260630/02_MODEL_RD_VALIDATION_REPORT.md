# Gate E Model R&D Validation Report - 2026-06-30

- Label rows available: 919
- Targets tested: 12
- Targets passing review-only validation bar: 12
- Minimum validation sample size: 75
- Worst empirical Brier score: 0.236779
- Minimum Brier improvement vs global baseline: 0.003549
- Calibration bucket rows: 46

All tested targets improved over the global-rate baseline in the historical
time-split validation. This supports review-only R&D feasibility, but the
model remains partial because features are limited to draft capital, class,
and position, and labels cover drafted players only.

Censored-window handling: first-3-year and first-5-year targets only used
calendar-complete windows. Missing labels were excluded, not treated as misses.
