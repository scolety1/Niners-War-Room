# Rookie Analyzer Ordering Refinement - 2026-06-13

## Verdict

Verdict: GREEN.

Stage 3 applies a safe analyzer-only ordering refinement. It does not create a score, does not change production rankings, does not change private scores, does not create probabilities or bands, does not wire app or Streamlit output, and does not use veteran outcome heads.

## Refinement

The analyzer now emits `analyzer_group` and sorts by that group before the existing candidate context.

Analyzer groups:

- `premium_review`
- `premium_manual_review`
- `round2_review`
- `round2_manual_review`
- `5_04_watch`
- `5_04_manual_review`
- `manual_review`
- `unavailable`
- `blocked`

This keeps the analyzer easier to scan by separating premium, Round 2, 5.04, manual-review, unavailable, and blocked rows. It is a display/export grouping only, not a private score or production rank replacement.

## Ordering Basis

Ordering remains deterministic from source-safe local exports:

- analyzer group;
- production-ready status;
- position;
- generated local `candidate_rank`;
- player name.

No ADP, public rankings, consensus, projections, fantasy forecasts, trade calculators, market values, draft-kit ranks, league rank, prior draft history, RotoWire rankings/projections, legacy `private_score`, probabilities, or bands are used.

## Guardrails Preserved

- `1.03` remains not forced open.
- `rankable_with_warning` rows keep visible warnings.
- `manual_review_required` rows remain separate from warning-rankable rows.
- `blocked` and `unavailable` rows remain non-actionable.
- Every row keeps `app_ready=no`.
- Every row keeps `production_score_created=no`.
- Every row keeps `probabilities_created=no`.
- `data/` remains untouched and uncommitted.
- `local_exports/` remains uncommitted.

## Stage 3 Gate

Stage 3 is GREEN if strict builds pass, the analyzer direct harness passes, the grouped analyzer export preserves required row markers, and only the Stage 3 tracked files are committed.
