# Rookie Shadow Ranking Export - 2026-06-13

## Purpose

Step 3 creates a rookie-only shadow ordering export from the Step 2 review-board outputs. It is intended for human review of how the v0.3 evidence might be grouped and ordered before any future decision work.

This is shadow/export-only. It does not create production rankings, private scores, formulas, app output, rookie probabilities, probability bands, outcome columns, or veteran outcome-head inputs.

## Inputs

The exporter reads only Step 2 review-board outputs from:

`local_exports/model_v4/rookie_framework_v02/review_board_v03/`

Required inputs:

- `rookie_review_board_v03.csv`
- `rookie_review_board_premium_review_v03.csv`
- `rookie_review_board_round2_v03.csv`
- `rookie_review_board_5_04_watchlist_v03.csv`
- `rookie_review_board_manual_flags_v03.csv`
- `rookie_review_board_remaining_gaps_v03.csv`
- `README_ROOKIE_REVIEW_BOARD_V03.md`

It does not read `data/`, app files, outcome-column files, veteran outcome-head files, production ranking files, private-score files, or formula files.

## Outputs

The exporter writes local-only outputs under:

`local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/`

Expected files:

- `rookie_shadow_ranking_v03.csv`
- `rookie_shadow_ranking_premium_v03.csv`
- `rookie_shadow_ranking_round2_v03.csv`
- `rookie_shadow_ranking_5_04_watchlist_v03.csv`
- `README_ROOKIE_SHADOW_RANKING_V03.md`

Generated local exports must not be committed.

## Required Row Markers

Every exported row must include:

- `promotion_status = shadow_only`
- `production_allowed = no`

Rows missing either marker fail validation.

## Shadow Ordering Rules

The script produces a deterministic `shadow_order` using Step 2 review metadata only:

- review bucket
- review status
- tag/role summary
- source confidence
- hard-cap presence
- remaining-gap count
- manual-flag count
- position
- player name
- player id

The ordering does not use ADP, public rankings, consensus, projections, market values, trade values, draft-kit ranks, prior league draft history, RotoWire rankings/projections, legacy `private_score`, rookie probabilities, or probability bands.

The `tag_summary` column is carried through from the Step 2 review board so role/archetype context remains visible in the shadow export. It is review context only and does not change production eligibility.

## Source Safety

- Prohibited source context from Step 2 remains in warning fields only.
- Strict mode rejects prohibited private input columns such as `private_score`, ADP, market, projection, probability, or band fields.
- Warning fields such as `prohibited_sources_detected` are preserved as warnings, not promoted.
- Hard caps, soft flags, manual-review flags, remaining gaps, source conflicts, and review status are carried forward.
- `tag_summary` is carried forward unchanged as review-only role/archetype context.

## What This Does Not Enable

This export does not enable:

- production ranking changes;
- final rookie rankings;
- private score changes;
- formula changes;
- Streamlit/app display;
- app-readable rookie outcome columns;
- rookie probabilities;
- probability bands;
- outcome-column files;
- veteran outcome-head usage;
- commits to `data/` or `local_exports/`.

## Next Gate

Any future move beyond this shadow export requires adversarial audit and explicit HQ approval. The default stance remains no production promotion.
