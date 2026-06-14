# Rookie Analyzer v0.3 Core Audit - 2026-06-13

## Executive Verdict

Verdict: GREEN.

Stage 1 created a rookie-only analyzer export that remains local-only, review-oriented, and non-production. No production ranking, private score, formula, app, Streamlit, probability, band, outcome, or veteran outcome-head surface was changed.

No blocker was found.

## Source Safety

The analyzer reads only local rookie framework exports:

- review board v0.3;
- shadow ranking v0.3;
- production-candidate v0.3.

Strict mode rejects prohibited private-value input columns, including ADP, public rankings, projections, consensus, market/trade values, draft-kit ranks, legacy `private_score`, probabilities, and bands. The only allowed internal order field from candidate inputs is generated `candidate_rank`.

`prohibited_sources_detected` remains warning context only. It is not used as positive private value.

## Output Counts

Full analyzer export:

- total rows: `211`
- `ready`: `0`
- `rankable_with_warning`: `42`
- `manual_review_required`: `7`
- `blocked`: `43`
- `unavailable`: `119`

Pick-zone counts:

- `1.03`: `0`
- `1.04`: `10`
- `2.08`: `9`
- `5.04`: `144`
- `pass/manual_add`: `48`

Split outputs:

- premium rows: `10`
- Round 2 rows: `9`
- 5.04 rows: `119`
- manual-review rows: `7`
- blocked/unavailable rows: `162`

These counts align with the production-candidate warning-status audit.

## 1.03 Handling

GREEN.

The analyzer has `0` rows with `pick_zone=1.03`. It does not backfill `1.04` into `1.03`, does not force a player into the pick, and does not create a hidden production recommendation.

Future docs may still describe `1.03` as trade-down/manual-review/no-player-cleared, but Stage 1 did not create a player row for it.

## 1.04 Warning Review

GREEN.

`1.04` rows remain warning-visible:

- `7` rows are `rankable_with_warning`.
- `2` rows are `manual_review_required`.
- `1` row is `unavailable`.
- `0` rows are clean `ready`.

The seven warning-rankable premium candidates have `best_pick_fit=1.04_premium_warning_visible` and non-empty warning context.

Manual-review premium rows remain held:

- Kaelon Black: `manual_review_required`
- Jordyn Tyson: `manual_review_required`

Ted Hurst remains `unavailable`.

## Round 2 / 5.04 Sanity

GREEN.

Round 2 rows:

- `3` `rankable_with_warning`
- `2` `manual_review_required`
- `4` `unavailable`

Round 2 rankable rows are labeled with practical RB/WR review fits rather than production readiness.

5.04 rows:

- `32` `rankable_with_warning`
- `3` `manual_review_required`
- `84` `unavailable`

The analyzer keeps 5.04 as asymmetric-dart/manual-context work. Blocked and unavailable rows are separated into `rookie_analyzer_blocked_v03.csv`.

## Warning Visibility

GREEN.

All `rankable_with_warning` rows have visible warning context. The audit found:

- `0` `rankable_with_warning` rows missing warnings;
- manual-review flags preserved;
- soft flags preserved;
- remaining gaps preserved;
- source caveats preserved;
- blocker context preserved.

The analyzer does not treat warning rows as clean ready rows.

## Implementation Safety

GREEN.

Confirmed:

- every analyzer row has `app_ready=no`;
- every analyzer row has `production_score_created=no`;
- every analyzer row has `probabilities_created=no`;
- no app-ready artifact was created;
- no production score was created;
- no probabilities or bands were created;
- no production rankings were changed;
- no private scores or formulas were changed;
- no Streamlit/app files were changed;
- no Outcome Columns HQ files were touched;
- no veteran outcome heads were touched;
- `data/` remains untracked and uncommitted;
- `local_exports/` remains uncommitted.

## Stage 2 Gate

Stage 2 is GREEN.

Stage 3 may proceed to ordering refinement, provided it remains analyzer/export-only and keeps all global guardrails intact.
