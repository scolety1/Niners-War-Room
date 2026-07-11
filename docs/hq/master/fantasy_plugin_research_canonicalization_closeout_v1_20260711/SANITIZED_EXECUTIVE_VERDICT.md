# Sanitized Executive Verdict

## Overall verdict

`YELLOW_PLUGIN_RESEARCH_USEFUL_WITH_SCORING_AND_GOVERNANCE_CAVEATS`

The completed audit found limited manual research value, but not enough semantic fidelity, context, freshness, source attribution, or rights clarity for production integration.

## Flaim

One 2026 Sleeper league connected successfully. The settings review produced 23 `EXACT`, 5 `PARTIAL`, and 2 `NOT_EXPOSED` results. Core scoring and starting-slot values were mostly explicit, while FLEX eligibility, full keeper/dynasty semantics, full playoff structure, and current phase-specific roster limits were incomplete or absent.

Ten roster calls were internally coherent. Stable provider player identifiers existed, and ownership was identifier-consumable, but ownership was not independently verified against same-time native truth. Free-agent retrieval was capped, alphabetic, noisy, incomplete, and unsuitable as a complete pool. Standings were materially misrepresented; add/drop normalization was materially unsafe; exact trade-side reconstruction was unsafe. Most records lacked adequate provider as-of or version fields.

Classification: `USEFUL_MANUALLY_NOT_READY_FOR_ADAPTER`

## FantasyBot

Eleven supported cases were each repeated twice, producing immediate exact repeatability of `11/11`. That result does not establish day-to-day, week-to-week, or provider-version stability.

Fidelity review produced 18 `FORMAT_MISMATCH`, 4 `CONTEXT_MISSING`, and 1 unsupported custom-scoring/dynasty-pick probe. No case established a validated useful external blind spot. Tested comparisons returned statistics rather than a dependable dynasty-value verdict, and tested trade outputs used season/PPR production totals rather than a comparable dynasty trade-value scale.

Exact NWR scoring, first-down rules, lineup scarcity, dynasty/keeper context, roster context, ownership, and draft-pick support were absent. Provider data timestamps, tool versions, underlying source attribution, and persistent-use rights were insufficient. No qualifying numerical signal was demonstrated.

Classification: `MANUAL_EXTERNAL_SECOND_OPINION_ONLY`

## External weighting and integration

- Production external influence: `0%`
- Research weight `2.5%`: `NOT_JUSTIFIED`
- Research weight `5%`: `NOT_JUSTIFIED`
- Numerical blend constructed: `NO`
- NWR base score: controlling and separately reproducible
- Flaim adapter: `BLOCKED`
- FantasyBot disagreement panel: `BLOCKED`
- FantasyBot ranking component: `BLOCKED_AT_0_PERCENT`
- Manual consultation: `PERMITTED_WITH_CAVEATS_AND_TERMS`
- Production use: `BLOCKED`
