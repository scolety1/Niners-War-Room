# Phase 10J External Research Intake

Date: 2026-05-17

## Raw Preservation

Newly uploaded research reports were copied unchanged into:

`local_exports/model_v4/raw_user_exports/deep_research/phase10_external_reports_20260517/`

Manifest:

`local_exports/model_v4/raw_user_exports/deep_research/phase10_external_reports_20260517/PHASE10_EXTERNAL_REPORTS_MANIFEST.csv`

Earlier Deep Research markdown reports remain preserved at:

- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-26-audit-framework.md`
- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-27-rookie-signals.md`
- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-28-inline-position-signals-summary.md`

## Report Classification

| Report | Model lane | Scoring allowed | Use |
|---|---|---:|---|
| Audit Checklist for a Local-First Dynasty Fantasy Football Data Pipeline | source governance | no | Harden source trust, identity joins, leakage checks, as-of integrity, and promotion gates. |
| Replacement-Level Value and VORP for a 10-Team 1QB Dynasty Fantasy Football League | formula design guidance | no | Inform replacement baselines, VOLS/VORP separation, first-down fallback labeling, and return-role treatment. |
| Veteran Dynasty Decision Framework | formula design guidance | no | Inform age/dropoff lanes, veteran confidence, sell/hold/shop labels, and market/private value separation. |
| Modeling First-Down and Return Scoring in Dynasty Fantasy Football | formula design guidance | no | Inform first-down module design, return scoring caps, return-era adjustments, and double-counting checks. |
| Designing an Audit Framework for a Dynasty Fantasy Football Valuation Model | audit governance | no | Inform pre-promotion audit structure, leakage budgets, rolling validation, and player-level receipt requirements. |
| Dynasty Rookie Signal Hierarchy for 10-Team 1QB Non-PPR | prospect prior guidance | no | Inform rookie/prospect priors and position-specific rookie feature design. |
| Rookie Metric Framework for a Local-First Dynasty Analyzer | prospect prior guidance | no | Inform rookie metric hierarchy, position-specific prospect weights, rookie-board format discounts, and confidence/uncertainty design. |
| Auditing a Dynasty Rookie Draft Model Data Stack | prospect data-stack audit guidance | no | Inform prospect feature-table readiness, historical label requirements, draft-capital and market baselines, and time-aware validation. |
| Inline 2026 1.08 vs 2027 first strategy report | market/strategy context only | no | Inform trade-decision explanation and liquidity context, not Dynasty Asset Value. |
| Inline position-signal hierarchy report | formula design guidance | no | Inform position-specific weighting direction and sanity fixtures. |

## Immediate Takeaways

The reports support the current data-spine direction:

- keep private football value built from observed production, usage, age, role, and licensed route/target/snap evidence
- keep projections, ADP, rankings, mock drafts, trade values, and league rank out of Dynasty Asset Value
- use market data only as context, sanity review, and trade-liquidity explanation
- compute league-adjusted value above replacement for this 10-team, 1QB, non-PPR, first-down format
- model rushing/receiving first downs directly where imported, and clearly label fallback estimates
- separate return scoring from core player talent and cap its dynasty contribution
- require stronger confidence penalties and review labels where evidence is missing, estimated, proxy-only, or source-limited
- keep veteran decisions format-aware, especially for aging RBs, no-premium TEs, and rushing QBs approaching rushing decline
- rookie/prospect modeling should stop broad collection, add historical NFL outcome labels if missing, and validate against draft-capital-only and market-only baselines
- rookie-board scoring should favor RB/WR in this format, heavily tax ordinary QBs in 1QB, and require exceptional receiving profiles before TE premiums appear
- prospect features should be time-safe, position-specific, and reported with uncertainty rather than false precision

## Formula-Phase Requirements

Before formula work, the model should have:

- source lanes enforced at column level
- no silent fuzzy joins
- no null-to-zero evidence conversion
- no market or projection leakage into private value
- replacement/VORP baselines explicit and configurable
- first-down and return scoring receipts visible
- rookie/prospect priors separate from NFL production evidence
- confidence and warning labels tied to missingness, proxy use, and estimated sections
- historical rookie backtests using chronological or leave-one-draft-class-out validation before trusting prospect formulas
- draft capital, ADP, and market consensus separated into factual prior, market context, and baseline-comparison lanes

## Status

The full external research set is admitted as research guidance only. These reports are not player evidence rows, not source production rows, and not formula outputs.
