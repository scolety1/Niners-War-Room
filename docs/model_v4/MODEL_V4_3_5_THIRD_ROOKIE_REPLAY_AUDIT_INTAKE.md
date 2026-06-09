# Model v4.3.5 Third Rookie Replay Audit Intake

## Source

User-pasted third-agent audit summary.

## Verdict From Report

`model likely viable, backtest/outcome coverage needs repair before tuning`

## Main Findings

- Early hit rates look discouraging mainly because of replay/outcome infrastructure, not necessarily because the core rookie formula is broken.
- Historical outcome labels are incomplete: 338 of 395 offensive rookies have labels.
- The replay universe is too broad if interpreted as a 10-team fantasy rookie draft.
- Hit definitions need to distinguish rookie-year, year-two, and year-three outcomes.
- 2024 and 2025 are immature and should not drive formula tuning too aggressively.
- Production/team-share may still overpower draft capital for day-three profiles.
- First-round WR floors may still need clearer support.
- TE values may need further no-premium damping.
- Confidence caps may need tightening when only one or two signals are strong.

## Current Status After Local Repair

Several audit concerns have already been addressed by the v4.3.5 replay-judgment repair:

- Added `Fantasy-Relevant Replay Pool`.
- Added broad, strict starter, and difference-maker hit labels.
- Added outcome maturity.
- Kept outcome labels display-only.
- Did not change formula weights.

## Remaining Candidate Work

Do not tune yet. The next safest work is:

1. Build a mature-years miss-pattern report for 2021-2023.
2. Separate top-ranked misses and low-ranked hits inside the fantasy-relevant replay pool.
3. Identify whether day-three production false positives repeat enough to justify formula changes.
4. Test confidence-cap changes before changing core component weights.
5. Revisit TE and first-round WR guardrails only after miss-pattern evidence is summarized.

## Do Not Do Yet

- Do not tune to consensus rankings.
- Do not treat unlabeled outcomes as misses.
- Do not use 2024/2025 as settled outcome truth.
- Do not apply formula changes before comparing the remaining deep research output.
