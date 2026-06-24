# NWR Unified Player Universe Contract V1

Date: 2026-06-24
Status: REVIEW-ONLY CONTRACT

## What This Artifact Is

`docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_review.csv` is a review-only generated artifact that combines currently available source layers into one inspectable player universe.

It is intended to help humans audit source coverage, rank-source separation, identity gaps, duplicate risks, age coverage, outcome coverage, market joins, and app-readiness blockers.

## What This Artifact Is Not

This artifact is not:

- an app source of truth.
- a Dynasty Rankings replacement.
- a Frozen Final Draft Board replacement.
- a model input.
- a rank/tier generator.
- a trade-value source.
- an approval to wire unified rows into Drafting Mode, Cheat Sheets, Live Draft Room, Player Compare, Trading Lab, Post-Draft Mode, or Settings/Data Health.

## Allowed Uses

- Review source coverage across veterans, rookies/prospects, frozen context, PDF free agents, market context, outcome context, identity, and age.
- Audit duplicate and identity gaps.
- Audit missing ages and missing player IDs.
- Evaluate whether a future unified-player-universe service is safe to build.
- Create a manual review queue for source prep.
- Feed future validation tests after explicit approval.

## Banned Uses

- Do not drive Dynasty Rank from this artifact.
- Do not replace the approved 240-row Full Dynasty source.
- Do not replace Frozen Final Draft Board V1.
- Do not use this artifact in app pages until a later explicit integration lane approves it.
- Do not give rookies/prospects fabricated veteran Dynasty Rank.
- Do not fabricate outcome probabilities.
- Do not fabricate player IDs.
- Do not use DynastyProcess, ADP, market rank, vendor rank, or projection values as model inputs, rank truth, tier truth, or default sort.
- Do not treat `unified_display_rank` as source truth.

## Source Layers

The review artifact uses these layers:

- Veteran Full Dynasty Layer: approved 240-row full dynasty source from ignored local source path.
- Rookie/Prospect Layer: Rookie HQ app props and frozen-board rookie context.
- Frozen Baseline Layer: 66-row frozen board checkpoint, represented as context plus dropped-veteran checkpoint rows.
- PDF Free-Agent Availability Layer: LVE PDF page-3 free-agent availability context.
- Market Baseline Layer: DynastyProcess display-only market context.
- Outcome Context Layer: approved display-only outcome columns where matched.
- Identity/Age Layer: player ID audit, manual review queue, and approved display-age audit artifacts.

## Rank-Source Policy

Rank source must be explicit.

Allowed rank-source labels:

- `FULL_DYNASTY_RANK`
- `ROOKIE_RANK`
- `FROZEN_BASELINE_RANK`
- `CANDIDATE_RANK`
- `UNRANKED_REVIEW`

Veteran Full Dynasty rows may carry `dynasty_rank` from the approved full dynasty source.

Rookie/prospect rows may carry `rookie_rank`, `frozen_baseline_rank`, and review-only `candidate_rank` only where those values already exist in approved/review-safe artifacts.

Rookie/prospect rows must not carry `dynasty_rank` unless a future separately approved unified dynasty rank source exists.

`unified_display_rank` is a generated review-order field. It is not source truth, not model truth, not Dynasty Rank, and not final board rank.

## Identity Policy

Preferred identity order:

1. Source-provided stable `player_id`.
2. High-confidence identity audit IDs.
3. Normalized name plus position for review grouping only.

Missing IDs are allowed but must be reported in `unified_player_universe_v1_identity_gap_review.csv`.

Low-confidence duplicates must not be auto-merged. Duplicate groups must be marked `REVIEW_NEEDED`.

## Age Policy

Age may be displayed only when an approved/review-safe source provides it.

Accepted age labels include:

- `NWR approved source`
- `rookie verified age audit`
- `DynastyProcess display fallback`
- `PDF derived display artifact`
- `Not enough information`

Missing age is not a player downgrade. It means the approved source contract does not currently provide a reliable age.

## Outcome Policy

Outcome context is display-only.

Missing or unsupported outcome rows must show `Not enough information`.

Outcome fields may not create:

- rank.
- tier.
- hidden sort.
- private value.
- model inputs.
- final advice.

## Market Baseline Policy

DynastyProcess market data is display-only.

Allowed market fields include:

- `dp_1qb_value`
- `dp_market_rank`
- `nwr_vs_market_gap`
- `market_match_status`

Market fields may not become rank truth, model inputs, default sort, hidden sort, or source-truth labels.

## Duplicate Handling

Duplicates are detected by:

- exact `player_id`.
- exact `normalized_name + position`.
- suffix-insensitive name differences.
- conflicting teams.
- conflicting positions.
- players appearing in multiple layers.

Duplicates are reported in:

`docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_duplicate_review.csv`

Do not auto-merge duplicates until a human review lane approves the merge policy.

## Missing-Data Handling

Use `Not enough information` when a trusted source does not provide a value.

Do not encode missing data as:

- zero.
- low probability.
- low rank.
- bad player.
- automatic downgrade.

Rows with missing IDs, missing ages, duplicate groups, low join confidence, or manual-review flags must remain visible and marked for review.

## App Wiring Gate Requirements

Before any app page may consume this artifact, a future integration lane must complete:

1. Contract approval.
2. Schema validation.
3. Duplicate review triage.
4. Identity gap triage.
5. Age coverage review.
6. Outcome coverage review.
7. Market display-only guardrail test.
8. Rank-source guardrail test.
9. Data Health integration.
10. Browser smoke on all affected pages.

Until then:

- `app_wiring_allowed` must be `no` on every row.
- `model_input_allowed` must be `no` on every row.

## Current V1 Review Artifact Counts

- Total rows: 383.
- Veteran rows: 252.
- Full Dynasty veteran source rows preserved: 240.
- Frozen dropped-veteran checkpoint rows: 12.
- Rookie/prospect rows: 54.
- PDF free-agent rows: 77.
- Duplicate review rows: 15.
- Identity gap review rows: 330.
- App wiring allowed rows: 0.
- Model input allowed rows: 0.

## Guardrail Confirmation

This contract and prototype do not change app behavior, model/rank logic, `final_board_rank`, Dynasty Rank, tier assignments, latest files, pinned snapshots, or Frozen Final Draft Board V1.
