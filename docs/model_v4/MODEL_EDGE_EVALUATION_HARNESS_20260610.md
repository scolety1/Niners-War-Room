# Model Edge Evaluation Harness - 2026-06-10

## Executive Read

NWR already has a real rookie replay lane, but it is mostly rookie-only. It is useful enough to study repeated hit/bust patterns before tuning rookie formulas. It is not yet enough to validate the full current-player dynasty board, veteran age curves, QB/TE caps, or established WR/RB dynasty horizon.

This pass added a small read-only harness layer:

- `src/services/model_edge_evaluation_harness_service.py`
- `scripts/build_model_edge_evaluation_harness.py`
- `local_exports/model_v4/model_edge/latest/model_edge_evaluation_harness_review_rows.csv`
- `local_exports/model_v4/model_edge/latest/model_edge_evaluation_harness_summary.csv`
- `local_exports/model_v4/model_edge/latest/model_edge_evaluation_position_summary.csv`

No active Rankings scores changed. Outcomes remain after-the-fact review only.

## Historical Classes Available

Available historical rookie classes:

| Source | Years | Rows | Status |
|---|---:|---:|---|
| `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv` | 2021-2025 | 395 | Main replay feature matrix |
| `local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv` | 2021-2025 | 395 | Outcome labels, display-only |
| `local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv` | 2021-2025 | 395 | Scored historical replay board |
| `sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv` | 2022-2024 | 60 | Lightweight fixture |
| `sample_data/historical_rookie_replay/post_draft_outcomes.csv` | 2022-2024 | 60 | Lightweight fixture outcomes |

Mature primary calibration rows are 2021-2023 only. 2024 is partial, and 2025 is too early.

New harness summary:

| Metric | Value |
|---|---:|
| Harness rows | 395 |
| Mature 3-year rows | 235 |
| Outcome-loaded rows | 338 |
| Future-stats-used-in-ranking rows | 0 |
| Difference-maker labels | 25 |
| Strong starter labels | 14 |
| Useful starter/flex labels | 38 |
| Bust labels | 131 |
| Too early to call labels | 130 |
| Outcome missing labels | 57 |

## Pre-Draft Inputs

The primary historical feature matrix contains:

- Identity and class fields: prospect key, name, position, college, NFL team, draft year, draft round, draft pick.
- Factual evidence JSON.
- Derived evidence JSON.
- Prospect prior evidence JSON.
- Context fields JSON.
- Market context JSON.
- Source status, receipts, and warning flags.

The current historical tuning service scores from source-safe fields such as production, college/team share, factual NFL draft capital, athletic prior, recruiting prior, and age lifecycle when available.

Important timing note: NFL draft capital is acceptable for post-NFL-draft dynasty rookie drafts, but it would be leakage for a pre-NFL-draft prospect model. The harness should store evaluation timing explicitly before future experiments.

## Post-Draft / Outcome Labels

Existing outcome outputs include:

- rookie-year points and PPG
- Year 2 points and PPG
- Year 3 points and PPG
- best 3-year PPG
- starter-level season count
- outcome label
- outcome maturity
- loaded season count
- warning flags

The current outcome-label service uses imported RotoWire fantasy stat rows. Those outcomes are useful for replay, but they must be checked against the league's exact scoring rules before being treated as final calibration truth. In particular, generic fantasy point totals may not perfectly encode no-PPR plus rushing/receiving first-down scoring.

## League-Specific Outcome Labels

The new harness maps existing outcome labels into review labels for this league:

- Difference-maker
- Strong starter
- Useful starter/flex
- Replacement-level
- Bust
- Injury/uncertain
- Too early to call
- outcome_missing

For rookies, evaluation windows should be kept separate:

- Year 1
- Years 1-2
- Years 1-3
- Best season in first 3 years
- Dynasty value retained after 2-3 years, if a source-safe internal value snapshot exists

The current repo has enough for a first pass at best-3-year and starter-season labels. It does not yet have a robust dynasty value retention label.

## Leakage Risks

Known safe/unsafe boundaries:

| Field family | Risk | Current handling |
|---|---|---|
| Outcome labels and RotoWire stat outcomes | High if used before ranking | Joined after ranking only |
| Market context JSON, ADP, public ranks, mocks | High | Must remain display/context only |
| NFL draft capital | Timing-sensitive | Safe only for post-NFL-draft rookie draft evaluation |
| Prior league draft history | Behavioral context only | Blocked from private value |
| Legacy active-pack private score | Contamination risk | Comparison-only |
| Roster/team tags | Bias risk | Display-only, tested neutral |
| Current active full-board scores | Not outcome labels | Cannot validate themselves without later outcomes |

The harness writes `blocked_use = active_private_score_input|active_rank_input|draft_recommendation|market_targeting|decision_board_action` on every evaluation row.

## What Is Testable Now

Currently testable:

- Historical rookie replay rank windows.
- Hit rates by top-5/top-10/top-20 windows.
- Position-level replay patterns.
- Rookie formula variants in shadow only.
- Draft-capital-only and simple-hybrid baselines against mature rookie rows.
- Repeated miss-pattern families.

Not yet testable with high confidence:

- Full current-player dynasty scores.
- Veteran age curves against dynasty value retention.
- RB/WR cross-position veteran balance.
- QB 1QB current-player cap against multi-year outcomes.
- TE no-premium current-player exception gates.
- Missing route/role evidence treatment for established stars.

## Current Formula Evaluation Gap

The current full-board credibility issues are mostly current-player problems, not pure rookie-replay problems. The repo needs a veteran/current-player historical harness with:

- historical season snapshots before each evaluation date
- league-scoring fantasy outcomes
- multi-year retained value labels
- age and career-mileage features
- injury/status and games-missed fields
- role and first-down components
- position-specific replacement and horizon labels
- clear evaluation-as-of date

Until then, current-player formula changes should be made through shadow experiments and human-review packets, not direct production tuning.

## New Harness Contract

The new harness supports:

- position
- draft year/class
- pre-draft profile feature summary
- private score at evaluation time
- eventual outcome label
- hit/bust classification
- rank buckets
- pick-range buckets
- position-specific analysis
- explicit leakage flags
- allowed/blocked use

The harness is intentionally read-only and does not alter active Rankings, Draft Prep, Live Draft Room, or Decision Board outputs.

## Next Harness Work

1. Build exact league-scoring outcome labels from raw weekly/player stats instead of generic fantasy point totals.
2. Add dynasty value retained labels for years 2-3.
3. Add a veteran/current-player replay harness.
4. Add QB/TE current-player cap replay using historical as-of snapshots.
5. Add a missing-evidence calibration audit: missing data should cap trust, not automatically crush established multi-year evidence.
