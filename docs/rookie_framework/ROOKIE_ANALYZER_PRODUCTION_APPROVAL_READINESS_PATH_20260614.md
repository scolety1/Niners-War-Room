# Rookie Analyzer Production Approval Readiness Path - 2026-06-14

## 1. Executive Verdict

The rookie analyzer is not implementation-ready for production/app integration now.

The rookie analyzer is not production-approved now.

What is safe to use today:

- local analyzer exports;
- local draft-day simulation exports;
- review-board, shadow-ranking, and production-candidate context;
- warning-visible manual review docs and checklists;
- production-approval planning documents.

What remains blocked:

- production ranking replacement;
- private-score changes;
- Streamlit/app wiring;
- app-readable rookie analyzer artifacts;
- rookie probabilities;
- probability bands;
- Outcome Columns HQ files;
- veteran outcome heads;
- hidden ranking or sorting keys;
- promotion of `rankable_with_warning` rows into clean `ready`.

The correct next move is a separate production-approval readiness path, not immediate app or production promotion.

## 2. Current Analyzer Capability

The rookie analyzer can currently provide local review context from v0.3 rookie artifacts:

- review-board export context;
- shadow-ranking export context;
- production-candidate status context;
- analyzer order and analyzer groups;
- warning-aware `rankable_with_warning` rows;
- `manual_review_required`, `blocked`, and `unavailable` separation;
- pick-fit fields for `1.03`, `1.04`, `2.04`, `2.08`, and `5.04`;
- trade-down and emergency-stop signals;
- draft-day simulation rows and pick cards when local exports are present.

Current analyzer state from the final checkpoint:

- total analyzer rows: `211`
- `ready`: `0`
- `rankable_with_warning`: `42`
- `manual_review_required`: `7`
- `blocked`: `43`
- `unavailable`: `119`

Analyzer groups:

- `premium_review`: `7`
- `premium_manual_review`: `2`
- `round2_review`: `3`
- `round2_manual_review`: `2`
- `5_04_watch`: `32`
- `5_04_manual_review`: `3`
- `unavailable`: `119`
- `blocked`: `43`

Draft-day simulation state:

- total simulation rows: `77`
- `1.03`: `1`
- `1.04`: `9`
- `2.04`: `10`
- `2.08`: `12`
- `5.04`: `45`
- pick cards: `5`

Every analyzer and simulation row remains local/export-only:

- `app_ready=no`
- `production_score_created=no`
- `probabilities_created=no`

Simulation rows also remain:

- `simulation_only=yes`

The analyzer can make review easier. It cannot make a production decision by itself.

## 3. Current Production Blockers

Football/source blockers:

- premium WR route, separation, press, YAC, target-earning, and first-down evidence still carries manual-review context;
- RB pass protection, contact balance, fumble, receiving, first-down, goal-line, and injury context still carries visible warnings;
- TE and QB exceptions remain narrow and manual, not broadly cleared;
- `1.03` remains unsupported and must not be forced open.

Manual-review blockers:

- seven rows remain `manual_review_required`;
- Jordyn Tyson still requires premium injury and role review;
- Kaelon Black still requires short-yardage and injury-history review;
- Round 2 injury/manual-review rows remain held;
- TE exception rows remain manual.

Source-safety blockers:

- quarantined market/rank/projection terms must remain warnings or excluded context only;
- manual-review-only evidence cannot become positive private value;
- soft secondary charting cannot open premium zones by itself;
- source conflicts must continue to block affected movement until resolved;
- ADP, rankings, consensus, projections, market, trade, draft-kit rank, public best-player lists, and legacy `private_score` remain prohibited as private inputs.

Missing-data blockers:

- many `5.04` rows remain unavailable because of low source confidence or missing role-path evidence;
- some profiles still need PFF/SIS/manual film confirmation;
- injury-history and role-path gaps remain unresolved for certain rows;
- Roster Declaration Day context may be needed before reducing late-profile uncertainty.

App/UI blockers:

- no app implementation exists;
- no feature flag exists;
- no app display contract has been implemented;
- no warning UX has been implemented;
- no production-facing representation of `1.03` has been implemented;
- no rollback switch has been implemented.

Testing/environment blockers:

- strict local builders and direct harnesses are available;
- pytest has been unavailable in this environment and must be accounted for before any production/app implementation;
- future integration needs tests for warning visibility, feature-flag isolation, marker preservation, and no dependency leakage into app/outcome/veteran paths.

Roster declaration / legal pool blockers:

- late watchlist rows may require Roster Declaration Day context;
- the legal production-facing pool has not been approved;
- blocked and unavailable rows remain non-actionable.

## 4. Approval Gates Before Implementation

Before any production/app integration, all gates below must be GREEN:

- Tim/HQ explicitly approves a separate implementation prompt.
- The implementation prompt names exact allowed files.
- An app display contract is approved.
- A feature flag or isolated display plan is approved.
- A rollback plan is approved before edits begin.
- Strict review-board, shadow-ranking, production-candidate, analyzer, and draft-day simulation builds pass.
- Direct harnesses pass.
- Pytest availability is resolved or HQ explicitly accepts direct-harness validation for the scoped task.
- No contamination blockers remain from ADP, rankings, consensus, projections, market, trade, draft-kit ranks, public best-player lists, or legacy `private_score`.
- No probabilities or bands are introduced unless separately approved under a new model contract.
- No veteran outcome heads are used.
- `rankable_with_warning` rows display visible warnings.
- `manual_review_required`, `blocked`, and `unavailable` rows remain visibly distinct.
- `1.03` remains no-player-cleared/trade-down/manual-review unless a later approved source-safe artifact opens it.
- `data/` and `local_exports/` remain uncommitted.

If any gate is missing, implementation must not start.

## 5. Recommended Implementation Shape If Later Approved

If HQ later approves implementation, the safest shape is:

- read the rookie analyzer or production-candidate export through a rookie-only adapter;
- display rookie analyzer order separately from existing production rankings;
- label the surface as rookie analyzer/review context unless HQ explicitly approves stronger wording;
- show `production_ready_status`, `tag_summary`, `warnings`, `blockers`, `source_confidence`, manual questions, `draft_only_if`, and `do_not_draft_if`;
- show `rankable_with_warning` separately from clean `ready`;
- keep `manual_review_required`, `blocked`, and `unavailable` visibly distinct;
- keep `1.03` as no-player-cleared/trade-down/manual-review when unsupported;
- leave existing `private_score` untouched;
- keep app integration feature-gated or isolated;
- default the feature off if app-facing;
- make rollback a one-flag disable plus artifact quarantine/removal;
- avoid probabilities and bands;
- avoid outcome-column promotion;
- avoid veteran outcome heads.

This is a proposal shape only. It is not approval to implement.

## 6. What Must Not Happen

Do not:

- overwrite or replace private scores;
- create a hidden sort key using market, rank, projection, consensus, ADP, trade, or draft-kit sources;
- create app-readable probability columns;
- create rookie probability bands;
- use veteran outcome heads;
- force rookies through veteran outcome heads;
- silently promote `rankable_with_warning` into clean `ready`;
- hide injury warnings;
- hide source warnings;
- hide manual-review warnings;
- hide blockers or remaining gaps;
- force `1.03` open;
- touch Outcome Columns HQ files;
- touch outcome probability files;
- modify Streamlit/app files without a separate HQ-approved implementation prompt;
- commit `data/`;
- commit `local_exports/`;
- push.

## 7. Recommended Next Human Decision

Recommended next human decision:

Approve a separate production-approval readiness review, not immediate implementation.

That review should decide whether Tim/HQ wants to:

- pause rookie lane until Roster Declaration Day;
- reduce the seven `manual_review_required` rows first;
- approve a separate app-integration proposal;
- approve a separate production implementation prompt with exact files, feature flag, tests, and rollback.

Default recommendation: pause rookie lane and use the analyzer locally as review-only until Tim/HQ explicitly approves one of those next steps.

Do not start the next task from this document.
