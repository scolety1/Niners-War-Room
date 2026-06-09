# Deep Research Prompt: Historical Rookie Model Calibration

Research how to evaluate and calibrate a dynasty rookie draft model for a 10-team, 1QB, non-PPR league with first-down scoring and no TE premium.

Do not assume consensus rankings are correct. The goal is to identify whether historical rookie formula signals are genuinely predictive and how to calibrate them without blindly copying market.

## Research Questions

1. From 2021-2025 NFL rookie classes, what signals best predicted fantasy-relevant dynasty hits at RB, WR, QB, and TE?
2. How predictive was NFL Draft capital by position and round?
3. When do college production and market share legitimately beat draft capital?
4. When do college production and market share create false positives, especially for late-capital WRs and RBs?
5. How should a 10-team 1QB league discount rookie QBs?
6. How should a no-TE-premium league treat rookie TEs, including elite TE prospects?
7. What historical examples resemble:
   - a first-round WR with mediocre college share but strong NFL capital,
   - a late-capital WR with huge production/team share,
   - a day-three RB with strong college production,
   - a productive TE in a no-premium format?
8. What backtest design is appropriate for rookie models?
9. What hit-rate thresholds are realistic for top 5, top 10, top 20 rookie-board picks?
10. What outcome labels should be used: year-one PPG, best first-three-year PPG, top-24 seasons, dynasty market value, or a blended outcome?

## League Format

- 10 teams
- 1QB
- non-PPR
- first-down scoring
- no TE premium
- return yards: 1 point per 30 yards
- return TD: 4 points

## Output Requested

Provide:

- recommended historical outcome labels
- realistic hit-rate expectations by draft-board window
- signal hierarchy by position
- draft-capital calibration suggestions
- production/team-share false-positive warnings
- examples from 2021-2025
- specific recommendations for whether to tune production, College Team Share, NFL Draft Pick Signal, athletic testing, age, QB discount, and TE cap
- guidance on whether a low hit rate means the model is bad or the backtest is under-labeled/misdesigned

Please be practical and ruthless. The owner is deciding whether to keep developing the model or bail.
