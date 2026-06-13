# Rookie Framework v0.3 Promotion Gates - 2026-06-13

## Purpose

This document defines future gates for rookie-only v0.3 work. It does not approve production use, rankings, probabilities, bands, app-readable outputs, outcome-column files, veteran outcome heads, private-score changes, formulas, or Streamlit changes.

## Gate 1: Review Board Export Only

Allowed outputs:

- Local-only or tracked review-board schema/artifact that shows evidence statuses, source provenance, manual-review flags, caps, tags, remaining gaps, and pick-zone context.
- Review-only labels such as `1.03_review`, `1.04_review`, `2.04_review`, `2.08_review`, `5.04_watch`, `manual_review`, `capped`, and `unavailable`.

Prohibited outputs:

- Final rankings, sorted draft boards, private scores, probabilities, bands, app-readable tables, production formulas, Streamlit wiring, outcome-column files, or veteran outcome-head inputs.
- Any use of ADP, public rankings, projections, consensus, fantasy forecasts, trade calculators, market values, draft-kit ranks, prior league draft history, RotoWire rankings/projections, or legacy `private_score` as private value.

Validation requirements:

- Row counts match the approved v0.3 candidate source or an explicitly documented review-only delta.
- All rows carry evidence status and source type.
- All soft/manual/conflict fields remain visible.
- `data/` and unrelated local exports are not staged or committed.
- No ranking/private-score/formula/app/outcome files change.

Stop conditions:

- Any market/rank/projection contamination.
- Any unexpected ranking/private score change.
- Any attempt to create rookie probabilities without approval.
- Any attempt to force rookies through veteran outcome heads.
- Any row-count break.
- Any unresolved source conflict affecting premium picks.

## Gate 2: Shadow Ranking Export Only

Allowed outputs:

- A shadow-only, non-production export that is explicitly labeled as review-only and not app-readable.
- Audit fields showing how evidence statuses, caps, source caveats, and manual-review flags affect shadow ordering or grouping.

Prohibited outputs:

- Production rankings, active Rankings hash changes, active private scores, app-readable display outputs, probability/band columns, veteran outcome-head inputs, formulas, Streamlit changes, or promoted model artifacts.
- Any hidden use of market, public ranking, projection, or consensus material.

Validation requirements:

- Shadow output is not wired to the app.
- Output is explicitly quarantined from production scoring and app display.
- Any ordering method is documented and adversarially reviewed before use.
- Source caveats and manual-review flags remain visible beside shadow context.
- Active ranking and private-score files are unchanged.

Stop conditions:

- Any market/rank/projection contamination.
- Any unexpected ranking/private score change.
- Any attempt to create rookie probabilities without approval.
- Any attempt to force rookies through veteran outcome heads.
- Any row-count break.
- Any unresolved source conflict affecting premium picks.

## Gate 3: Adversarial Audit

Allowed outputs:

- Audit reports, findings tables, do-not-promote lists, source-safety matrices, and safe patch queues.
- Local-only audit artifacts or tracked audit docs, when scoped to rookie framework files.

Prohibited outputs:

- Production promotions, app wiring, probability or band generation, ranking/private-score/formula changes, outcome-column files, veteran outcome-head files, or data commits.

Validation requirements:

- Confirm contamination blockers are zero or document blockers and stop.
- Confirm secondary charting did not become hard private evidence without policy approval.
- Confirm scouting prose was not converted into numeric grades.
- Confirm injury notes did not change caps or pick zones without policy approval.
- Confirm 1.03, 1.04, 2.04, 2.08, and 5.04 row counts match expected source artifacts.
- Confirm premium-pick source conflicts are resolved or explicitly blocked.

Stop conditions:

- Any market/rank/projection contamination.
- Any unexpected ranking/private score change.
- Any attempt to create rookie probabilities without approval.
- Any attempt to force rookies through veteran outcome heads.
- Any row-count break.
- Any unresolved source conflict affecting premium picks.

## Gate 4: HQ Approval

Allowed outputs:

- HQ decision memo, lane status update, or explicit approval/hold/block record.
- Narrow follow-up task definition for the next rookie-only step.

Prohibited outputs:

- Any code or artifact promotion that exceeds the approved HQ decision.
- Any app, ranking, scoring, probability, band, formula, outcome-column, or veteran outcome-head change unless HQ explicitly names and approves it.

Validation requirements:

- HQ approval must identify the exact gate passed and exact allowed files/actions.
- Approval must state whether outputs remain local-only, tracked-doc only, shadow-only, or eligible for a future implementation step.
- Approval must preserve the source-safety prohibitions unless explicitly superseded by a documented new policy.

Stop conditions:

- Any market/rank/projection contamination.
- Any unexpected ranking/private score change.
- Any attempt to create rookie probabilities without approval.
- Any attempt to force rookies through veteran outcome heads.
- Any row-count break.
- Any unresolved source conflict affecting premium picks.

## Gate 5: Production/App Promotion

Allowed outputs:

- None by default. Production/app promotion requires a future, explicit HQ-approved release gate and a separate implementation contract.

Prohibited outputs:

- Rookie probabilities or bands.
- App-readable rookie outcome columns.
- Streamlit/app wiring.
- Active rankings, private scores, or production formulas.
- Veteran outcome-head usage.
- Outcome-column files.
- Promoted model artifacts.

Validation requirements:

- A future release gate must define exact source hierarchy, schema, tests, artifact paths, app behavior, rollback plan, and audit signoff.
- Tests must prove no forbidden inputs entered private value.
- Tests must prove no veteran outcome heads are used.
- Tests must prove row counts and premium-pick source conflicts are clean.
- HQ must explicitly approve production/app promotion after adversarial audit.

Stop conditions:

- Any market/rank/projection contamination.
- Any unexpected ranking/private score change.
- Any attempt to create rookie probabilities without approval.
- Any attempt to force rookies through veteran outcome heads.
- Any row-count break.
- Any unresolved source conflict affecting premium picks.

## Current Recommendation

The next safe step is Gate 1 only: create a rookie review-board export from v0.3 candidate artifacts, still review-only, with no rankings, probabilities, bands, app promotion, outcome-column files, or veteran outcome-head usage.
