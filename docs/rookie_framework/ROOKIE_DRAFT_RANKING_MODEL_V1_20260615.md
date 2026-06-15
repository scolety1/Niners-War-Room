# Rookie Draft Ranking Model v1

Date: 2026-06-15

Status: local-only manual rookie draft ranking board. Not production-approved.

## What Was Built

Created a rookie-only manual draft ranking model:

- `scripts/rookie_framework/build_rookie_draft_ranking_v01.py`
- `tests/test_rookie_draft_ranking_v01.py`

The model produces a true rookie draft ranking board for Tim's league format:

- 10-team dynasty/keeper hybrid
- 1QB
- non-PPR
- 0.4 rush/receiving first-down scoring
- passing TD devalued at 3 points
- rush/receiving TD at 4 points
- return scoring noted only where available

## Local Inputs

The ranking model uses:

- repaired rookie analyzer rows from `local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03/rookie_analyzer_v03.csv`
- source-safe normalized rookie feature context from `local_exports/model_v4/rookie_framework_v02/normalization_pass_02/normalized_feature_view_v02_pass02.csv`

It does not read `data/`.

## Local Outputs

Created under:

`local_exports/rookie_framework/draft_ranking_model_v1_20260615/`

Outputs:

- `rookie_draft_ranking_v1_20260615.csv`
- `rookie_draft_ranking_v1_rb_20260615.csv`
- `rookie_draft_ranking_v1_wr_20260615.csv`
- `rookie_draft_ranking_v1_te_20260615.csv`
- `rookie_draft_ranking_v1_qb_20260615.csv`
- `rookie_star_watchlist_v1_20260615.csv`
- `rookie_bust_risk_watchlist_v1_20260615.csv`
- `rookie_manual_review_before_pick_v1_20260615.csv`
- `rookie_market_overlay_v1_20260615.csv`
- `README_ROOKIE_DRAFT_RANKING_MODEL_V1_20260615.md`

These exports are local-only and must not be committed.

## Ranking Components

The model creates ordinal local indexes:

- `star_upside_index`
- `bust_risk_index`
- `early_role_index`
- `long_term_value_index`
- `scoring_fit_index`
- `evidence_confidence_index`
- `positional_adjustment_index`
- `warning_penalty_index`
- `final_rookie_rank_score`

`final_rookie_rank_score` is an experimental rookie-only local ordering score. It is not a production private score, not a probability, not a band, and not an app-readable artifact.

## Star Capture

Star capture is modeled through:

- high-end archetype tags such as premium RB, three-down RB, target-commanding TE, true alpha or target-earning WR;
- source-safe production indicators such as rushing/receiving output, target share, touch share, and TD context;
- factual draft capital and landing spot fields where available;
- league scoring fit.

## Bust Avoidance

Bust avoidance is modeled through:

- visible warnings and remaining gaps;
- low source confidence;
- manual-review status;
- blocked or unavailable status;
- TE replacement tags;
- 1QB quarterback devaluation;
- source-limited 5.04 profiles receiving extra bust-risk pressure.

The model does not hide warnings to make a row look clean.

## ADP / Market Overlay

ADP/market is isolated.

No local player-level ADP or market rank source was admitted into this run. The overlay file is present as schema-only and every row states that market data is unavailable.

ADP, public rankings, consensus, projections, trade calculators, and market values do not feed `final_rookie_rank_score`.

## What Tim Can Use Now

Tim can use the ranking board manually as a draft-room ordering tool if warnings are visible. It is safer than the prior analyzer table because it explicitly balances star upside and bust risk, and it ranks all 211 rookie rows into a single manual board.

He should still treat:

- `manual_review_required` as a stop sign;
- `unavailable` and `blocked` as non-actionable;
- 5.04 source-limited rows as late darts only;
- 1.03 as trade-down/manual-review unless separately approved.

## What Remains Blocked

Still blocked:

- production ranking integration;
- private-score replacement;
- app/Streamlit wiring;
- probabilities;
- bands;
- outcome columns;
- veteran outcome heads;
- hidden sort keys;
- promoted artifacts.

## Commands Run

```powershell
python scripts/rookie_framework/build_rookie_draft_ranking_v01.py
python tests/test_rookie_draft_ranking_v01.py
```

Full validation also included the existing rookie strict builders and harnesses listed in the final overnight report.

## Rollback Path

Rollback is simple:

- stop using the local exports under `local_exports/rookie_framework/draft_ranking_model_v1_20260615/`;
- revert the commit containing `build_rookie_draft_ranking_v01.py`, its test, and this doc;
- the repaired analyzer pipeline remains independent.
