# Model v4.3.5 Deep Research Rookie Calibration Intake

## Source

User-provided deep research report: `C:/Users/codex-agent/Downloads/deep-research-report (9).md`

## Bottom Line

The report is not a recommendation to abandon the project. It is a recommendation to keep developing the model only if it becomes a probability-calibrated, position-specific decision engine anchored by NFL Draft capital.

It is a warning against using college production or team share as a default reason to push Day 3 players over premium NFL capital.

## Major Requirements

- Keep NFL Draft capital as the base-rate anchor, especially at WR and QB.
- Let college production and team share modify players mostly inside or near draft-capital tiers.
- Allow late-capital outliers, but treat them as low-base-rate tail outcomes.
- Use position-specific logic for RB, WR, QB, and TE.
- Use exact league scoring for outcomes.
- Evaluate mature 2021-2023 classes separately from partial 2024 and rookie-year-only 2025.
- Compare against draft-capital-only, market-only, and simple hybrid baselines before claiming edge.
- Use probabilistic evaluation, not only rank order.

## Recommended Outcome Labels

- Primary continuous label: best first-three-year PPG in exact league scoring.
- Secondary hit label: at least one startable positional season in Years 1-3.
- Ceiling label: at least one elite positional season in Years 1-3.
- Market label: optional sanity check only, not a model target.

## Position Signal Hierarchy

### WR

- Draft capital is the base rate.
- Age/early breakout and receiving yard share are major modifiers.
- College share should refine projections, not replace NFL capital.
- Day 3 WR hits exist but should be modeled as rare tail outcomes.

### RB

- Draft capital matters, but production can beat capital more often than at WR.
- Receiving profile and workhorse evidence are especially important.
- Rushing share without receiving should not be enough by itself.

### QB

- In 10-team 1QB, only top-end capital plus rushing or a clear immediate-start path should threaten early rookie-board value.
- Apply a major 1QB haircut.

### TE

- Use a hard no-premium TE cap.
- Break the cap only for rare profiles with elite capital/receiving role.
- Most TEs should be patience assets, not top-board priorities.

## Direct Implications For Current Model

- Skyler Bell-style profiles should be labeled as outlier/tail bets, not safe first-round alternatives.
- Carnell Tate-style profiles should benefit from strong Round 1 capital even if college share is not dominant.
- Kenyon Sadiq/Bowers-type profiles can be exceptions, but TE values need very clear no-premium labels.
- Emmett Johnson/Bucky Irving-style RB profiles can retain upside because receiving plus workload can beat weaker capital.

## Already Addressed Locally

- Added `Fantasy-Relevant Replay Pool`.
- Added broad, strict starter, and difference-maker hit labels.
- Added `Outcome Maturity`.
- Kept outcome labels display-only.
- Preserved market/projection/ranking exclusion from private value.

## Remaining Candidate Work

1. Build a mature 2021-2023 miss-pattern report.
2. Add capital-only and simple hybrid baselines for comparison.
3. Add by-position replay summaries.
4. Consider probability buckets/calibration tables instead of only ranks.
5. Only then test formula changes.

## Do Not Do

- Do not tune to consensus rankings.
- Do not turn market value into a primary target.
- Do not use college team share as a default reason to rank Day 3 WRs above Round 1 WRs.
- Do not treat 2024 and 2025 as fully mature outcome truth.
