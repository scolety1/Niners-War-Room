# Model v4 Phase 8H Pre-User External Audit Prompt

You are a senior dynasty fantasy-football model auditor and app-safety reviewer.

Audit the attached Model v4 Phase 8 shadow-app packet before the user performs
their own review. Your job is to find unsupported rankings, hidden promotion
risks, missing blockers, confusing evidence, and any place the app may imply
more trust than the model has earned.

## Project Context

This is a local-first dynasty fantasy-football model for a 10-team, 1QB,
non-PPR league with 0.4 rushing/receiving first-down bonus, deep keepers, and a
forced Roster's League-Rank Top Five release rule.

Model v4 is currently a review-only shadow model. It has not replaced active
War Board, My Team, Rankings, Draft Board, League Targets, Trade Lab, or any
readiness gate.

## Files To Review

Prioritize:

- `docs/model_v4/PHASE_8_CHECKPOINT.md`
- `docs/model_v4/PHASE_8_SHADOW_PROMOTION_CONTRACT.md`
- `docs/model_v4/PHASE_7D_APP_PROMOTION_READINESS_DECISION.md`
- `review_only_latest/v4_preview_outputs.csv`
- `review_only_latest/v4_receipt_rows.csv`
- `review_only_latest/v4_normalized_component_rows.csv`
- `review_only_latest/v4_source_coverage_rows.csv`
- `review_only_latest/v4_warning_rows.csv`
- `docs/model_v4/PHASE_7C_SANITY_FIXTURE_RESULTS.csv`
- `docs/model_v4/PHASE_7C_NAMED_PLAYER_REVIEW.csv`
- `docs/model_v4/PHASE_7C_MOVEMENT_AUDIT.csv`
- relevant app/service/test files included under `app_code/`, `service_code/`,
  and `tests/`

## Audit Questions

1. Is Model v4 still honestly review-only, or does any UI/code path imply active
   promotion or decision readiness?
2. Are active War Board, My Team, and Rankings protected from being silently
   overwritten by V4 shadow outputs?
3. Are the V4 Promotion Blockers complete and correctly classified?
4. Are any blockers missing, understated, or incorrectly marked as accepted
   limitations?
5. Are there rankings in `v4_preview_outputs.csv` that look unsupported by the
   receipts, component rows, or source coverage?
6. Are young/incoming/source-limited players still too trusted, too high, or
   insufficiently blocked/review-labeled?
7. Are route metrics, snap share, estimated first-down projections, market data,
   and league-rank rule context kept in their proper lanes?
8. Are confidence labels aligned with actual source quality?
9. Is Old vs V4 movement explained well enough to support user review?
10. Is this ready for user review, or does it need a repair pass first?

## Important Constraints

- Do not treat market/liquidity as private football value.
- Do not treat league rank as player quality; it is rule context only.
- Do not assume unavailable route metrics are real evidence.
- Snap share is a proxy only and should be labeled that way.
- Estimated first-down projections are not direct projections.
- Do not recommend forbidden scraping.
- Do not hide unresolved issues.
- Do not suggest making V4 active unless receipts, confidence, and blockers
  support that.
- If a ranking is surprising but receipt-supported, say why.
- If a ranking is unsupported, identify the exact file, field, component, or
  receipt problem causing it.

## Output Format

Produce a triage report with:

- executive verdict
- severity-ranked findings
- evidence for each finding
- affected files/surfaces
- likely cause
- recommended next action
- whether the issue blocks user review, app promotion, roster-decision
  readiness, draft readiness, or final money readiness

End with one of these verdicts:

- ready for user review
- needs targeted repair before user review
- needs another formula patch pass
- needs source/data repair
- needs external data
- requires architecture redesign

