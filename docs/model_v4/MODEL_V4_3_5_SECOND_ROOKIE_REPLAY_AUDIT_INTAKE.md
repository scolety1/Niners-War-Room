# Model v4.3.5 Second Rookie Replay Audit Intake

## Source

User-provided report: `C:/Users/codex-agent/Downloads/Rookie Replay Audit.docx`

## Verdict From Report

The report identifies repeated miss patterns rather than judging consensus alignment. It argues that the model needs stronger historical replay controls, clearer hit definitions, confidence caps, and positional calibration for a 10-team, 1QB, non-PPR, first-down league.

## High-Signal Takeaways

- Backtest outcome definitions must separate broad usable outcomes from strict starter or difference-maker outcomes.
- Replay universe should focus on fantasy-relevant rookie-draft candidates, not every offensive player drafted by the NFL.
- Mature historical years should be evaluated separately from partial/rookie-year-only outcomes.
- Late-capital production profiles should be labeled as high-variance model edges rather than treated as safe bets.
- Confidence caps should be stricter when a player has only one or two strong signals.
- TE and QB values must stay disciplined for 1QB and no TE-premium settings.

## Lower-Confidence Or Not Directly Applicable

- Several examples are outside the 2021-2025 replay window or are generic historical references.
- Some recommendations rely on post-draft rookie-year production, which should not affect pre-draft rookie draft ranks.
- The report contains tension between reducing first-round WR credit and adding first-round WR floor/early breakout handling. This should be tested through miss-pattern evidence rather than applied directly.
- Injury, offensive line, and detailed separation data are useful but not currently admitted as reliable formula inputs.

## Current Status After Repair

The replay judgment repair already addresses several core report concerns:

- `Fantasy-Relevant Replay Pool` added.
- `Broad Outcome Hit?`, `Strict Starter Hit?`, and `Difference Maker?` added.
- `Outcome Maturity` added.
- Outcome labels remain display-only.
- Formula weights were not changed.

## Do Not Do Yet

- Do not tune formulas directly from this report.
- Do not use public consensus or generic historical examples as player evidence.
- Do not apply post-draft early-production overrides to pre-draft rookie ranks.

## Candidate Next Actions After Remaining Audits Return

1. Build a miss-pattern report limited to mature 2021-2023 fantasy-relevant replay rows.
2. Compare top-ranked misses and low-ranked hits by position, draft round, and component shape.
3. Test confidence-cap changes before changing component weights.
4. Only consider formula tuning if the same failure pattern repeats across multiple mature classes.
