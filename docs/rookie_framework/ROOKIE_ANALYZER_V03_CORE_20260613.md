# Rookie Analyzer v0.3 Core - 2026-06-13

## Status

Stage 1 creates the first rookie analyzer export.

This is analyzer/export-only. It does not implement production promotion, replace production rankings, change private scores, modify formulas, wire app or Streamlit output, create rookie probabilities, create probability bands, touch Outcome Columns HQ files, or use veteran outcome heads.

## Inputs

The analyzer reads local-only rookie framework exports:

- Review board v0.3 exports from `local_exports/model_v4/rookie_framework_v02/review_board_v03/`
- Shadow ranking v0.3 exports from `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/`
- Production-candidate v0.3 exports from `local_exports/model_v4/rookie_framework_v02/production_candidate_v03/`

It must not read `data/`, production ranking files, app files, private-score files, formula files, probability files, band files, outcome files, or veteran outcome-head files.

## Outputs

The analyzer writes local-only exports to:

`local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03/`

Expected files:

- `rookie_analyzer_v03.csv`
- `rookie_analyzer_premium_v03.csv`
- `rookie_analyzer_round2_v03.csv`
- `rookie_analyzer_5_04_v03.csv`
- `rookie_analyzer_manual_review_v03.csv`
- `rookie_analyzer_blocked_v03.csv`
- `rookie_analyzer_readme.md`

Generated local exports must not be committed.

## Required Row Fields

Each analyzer row includes:

- `analyzer_rank`
- `analyzer_group`
- `player_id`
- `player`
- `position`
- `school`
- `pick_zone`
- `production_ready_status`
- `tag_summary`
- `source_confidence`
- `warnings`
- `blockers`
- `evidence_summary`
- `remaining_gaps`
- `best_pick_fit`
- `draft_only_if`
- `do_not_draft_if`
- `why_ranked_here`
- `why_not_higher`
- `why_not_lower`
- `app_ready`
- `production_score_created`
- `probabilities_created`
- `analyzer_notes`

## Required Row Markers

Every row must include:

- `app_ready = no`
- `production_score_created = no`
- `probabilities_created = no`

Rows missing these markers fail validation.

## Analyzer Behavior

The analyzer gives Tim practical draft-day review context. It keeps the production-candidate order separate from production rankings and adds manual decision prompts:

- `analyzer_group` separates premium review, Round 2 review, 5.04 watchlist, manual-review, unavailable, and blocked rows without creating a score.
- `best_pick_fit` describes the safest review use for the row.
- `draft_only_if` names the condition that must be true before using the row.
- `do_not_draft_if` names the clearest stop condition.

Rows marked `rankable_with_warning` remain warning-visible. They are not treated as clean `ready` rows.

Rows marked `manual_review_required` are split into `rookie_analyzer_manual_review_v03.csv`.

Rows marked `blocked` or `unavailable` are split into `rookie_analyzer_blocked_v03.csv` and remain non-actionable.

## Guardrails

- `1.03` remains not forced open when unsupported.
- No ADP, public rankings, consensus, projections, fantasy forecasts, trade calculators, market values, draft-kit ranks, league rank, prior draft history, RotoWire rankings/projections, or legacy `private_score` fields may be used as private-value inputs.
- `prohibited_sources_detected` may remain as warning context only.
- Secondary charting remains soft-flag context.
- Scouting prose remains manual-review context.
- No rookie probabilities or probability bands are created.
- No app-ready output is created.
- No production score is created.
- No veteran outcome heads are used.
- `data/` remains untouched and uncommitted.
- `local_exports/` remains uncommitted.

## Strict Mode

Strict mode fails on:

- missing review, shadow, or production-candidate inputs;
- prohibited private-value input columns;
- `data/` input or output paths;
- `app_ready=yes`;
- `production_score_created=yes`;
- `probabilities_created=yes`;
- unsupported `1.03` population;
- `rankable_with_warning` rows without visible warning context.

## Stage 1 Verdict

Stage 1 is GREEN only if:

- the review-board strict build passes;
- the shadow-ranking strict build passes;
- the production-candidate strict build passes;
- the analyzer strict build passes;
- direct harnesses pass;
- only Stage 1 tracked files are committed;
- `data/` and `local_exports/` remain uncommitted.
