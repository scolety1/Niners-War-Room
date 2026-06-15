# Rookie Analyzer Output Guide - 2026-06-13

## Purpose

The rookie analyzer is a local review export for draft-day context. It is not a production ranking file, not a private-score replacement, not an app-readable artifact, not a probability model, and not a veteran outcome-head input.

## How To Read `analyzer_rank`

`analyzer_rank` is a deterministic analyzer order for review. It is built from source-safe local exports and grouped by analyzer context:

- premium review;
- premium manual review;
- Round 2 review;
- Round 2 manual review;
- 5.04 watch;
- 5.04 manual review;
- unavailable;
- blocked.

It does not use ADP, public rankings, projections, consensus, market values, trade values, draft-kit ranks, legacy `private_score`, probabilities, or bands.

## Why Warnings Are Visible

Warnings are the point of the analyzer. A player can be useful to review while still carrying unresolved context.

Visible warning fields include:

- `warnings`
- `blockers`
- `remaining_gaps`
- `draft_only_if`
- `do_not_draft_if`
- `emergency_stop_signal`

Warnings must not be hidden to make a player look clean.

## Why `ready` Can Remain 0

`ready=0` is acceptable and currently expected. It means no row is clean enough to lose all warnings, manual-review context, remaining gaps, source caveats, and blockers.

The analyzer can still be useful because `rankable_with_warning` rows can be reviewed while warnings stay visible.

## How `rankable_with_warning` Works

`rankable_with_warning` means:

- the row can stay in analyzer order;
- the row is not clean `ready`;
- visible warnings must remain attached;
- the row is not approved for production implementation;
- the row does not create app-ready output;
- the row does not create probabilities or bands.

If the warning would affect a real pick decision, Tim must review it before using the player.

## How To Use Pick-Fit Fields

Pick-fit fields are manual context:

- `fit_1_03`: keeps `1.03` as trade-down/manual-review only when unsupported.
- `fit_1_04`: describes whether a row is a premium fit, manual hold, unavailable, blocked, or not a 1.04 fit.
- `fit_2_04` and `fit_2_08`: describe Round 2 RB/WR/exception fit with visible warnings.
- `fit_5_04`: describes late dart, stash, manual-hold, unavailable, or blocked context.
- `best_pick_fit`: summarizes the row's safest review use.
- `trade_down_signal`: tells Tim when the slot should be treated as a trade-down/manual-review context, not a market value.
- `emergency_stop_signal`: marks a stop condition such as blocked, unavailable, manual review, injury review, or source conflict.

These fields are not scores.

## Required Safety Markers

Every analyzer row must keep:

- `app_ready=no`
- `production_score_created=no`
- `probabilities_created=no`

Rows missing any of those markers fail validation.

## What Not To Treat As Production

Do not treat any analyzer field as:

- final rookie ranking;
- production ranking replacement;
- private score;
- probability;
- probability band;
- app-readable output;
- trade value;
- market signal;
- veteran outcome-head input.

The analyzer is a review tool only.
