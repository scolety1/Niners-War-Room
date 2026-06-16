# Sprint 5DE: Phase 7 Outcome Display Contract Planning

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROPOSE_LOCAL_ONLY_DISPLAY_CONTRACT_ARTIFACT_SPRINT`

Sprint type: `DISPLAY_CONTRACT_PLANNING_ONLY_NO_APP_WIRING_NO_NUMERIC_DISPLAY`

## 1. Scope

Sprint 5DE defines a planning-only display contract for how the Outcome Column may eventually be presented safely. This sprint does not create app-readable outputs, does not wire the app, and does not approve numeric display.

This sprint did not train models, create production model artifacts, run current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

No script was created. No local-only export was created.

## 2. Inputs Reviewed

5DE starts from the completed Phase 6 local-only production-candidate packet through:

- `5CZ` Phase 6 local-only production-candidate harness
- `5DA` Phase 6 local-only production-candidate historical modeling
- `5DB` Phase 6 production-candidate calibration and sanity audit
- `5DC` Phase 6 production-candidate model card and human-review packet
- `5DD` Phase 7 display-contract readiness verdict

Last completed commit:

`ebf57d3 Record Phase 7 display contract readiness`

Phase 7 may be proposed next as display-contract planning only. App wiring and all numeric display paths remain blocked.

## 3. Safest First User-Facing Concept

Recommended first user-facing Outcome Column concept:

`status_only_outcome_model_available_after_review`

The safest first display concept is non-numeric status only. It should communicate whether an Outcome model signal has passed internal review for a limited head family, without showing a probability, band, score, ranking, or hidden sortable value.

Recommended copy family:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: not available`

This copy family is intentionally qualitative and does not expose head-specific probabilities, confidence percentages, coarse probability bands, or model scores. It must not imply exact odds or rank players.

## 4. Display Options Decision

| Option | 5DE stance | Reason |
| --- | --- | --- |
| Non-numeric status only | safest first concept | Preserves uncertainty and avoids fake precision |
| Qualitative confidence language | future gated option only | Could still imply model precision or ranking if worded poorly |
| Internal-only review labels | approved to propose as local-only artifact next | Useful for review before app output exists |
| Exact percentages | blocked | Calibration gaps remain too large for player-facing odds |
| Coarse display bands | blocked, future gated option only | Bands may imply calibrated buckets before display semantics are proven |
| App-readable outputs | blocked | No output contract or app audit has approved them |
| App wiring | blocked | No UI implementation sprint is approved |

## 5. Numeric Display Policy

Exact percentages remain blocked.

No Phase 7 planning artifact may create, serialize, promote, or expose exact probability percentages. This includes visible UI percentages, hidden percent columns, JSON probability fields, CSV probability columns, model-card player rows, or any app-loadable field that can be interpreted as a player probability.

Coarse display bands remain blocked.

Coarse bands may be discussed only as a future gated option. They must not be generated, stored in app-readable form, wired into the app, or used as hidden sort or ranking signals in this sprint.

## 6. App-Readable Output Policy

App-readable probability, band, and status outputs remain blocked.

5DE does not approve creating any app-readable table, loader input, service output, release artifact, Streamlit file, player-card field, ranking/sorting input, hidden sort key, or promoted artifact. A later sprint must define a precise output schema, location, quarantine rule, app import audit, and rollback plan before any app-readable output can be proposed.

## 7. Eligible Heads For Future Display Consideration

Only these Phase 6 accepted heads may be considered in a future display-contract artifact sprint:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Eligibility here means eligible for display-contract planning only. It does not approve current-player inference, app-readable output, numeric display, sorting, ranking, hidden keys, or promotion.

## 8. Caution, Deferred, And Blocked Head Policy

Caution heads remain excluded:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Deferred heads remain deferred:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads remain blocked:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

A future display-contract artifact sprint must fail closed if any caution, deferred, blocked, unknown, or unapproved head is included.

## 9. Minimum Human-Review Requirements

Before any display sprint can be proposed, human review must confirm:

1. accepted head list matches the 5DB/5DD accepted set
2. caution, deferred, and blocked heads remain excluded
3. calibration caveats are visible in the contract
4. exact percentages remain blocked
5. coarse bands remain blocked unless explicitly scoped as future-only planning
6. copy avoids precise odds, ranking semantics, and false certainty
7. no hidden field can be used for sorting or ranking
8. no app-readable schema is created without a separate app-import audit
9. no current-player inference has run
10. no local-only evidence is promoted or committed

Human review must sign off before any Phase 8 app-wiring sprint can even be proposed.

## 10. Copy And UX Rules To Prevent Fake Precision

Required copy/UX rules:

- avoid percentages, decimals, odds, ranks, and score-like values
- avoid terms such as `likely`, `lock`, `safe`, `best`, `top`, or `edge` unless separately reviewed
- use status language instead of prediction language
- avoid color systems that imply probability buckets
- avoid sort controls, filter chips, badges, or tooltips that expose model ordering
- avoid comparing players by Outcome model status
- show no hidden model field in the DOM, exported table, or app state
- preserve existing status-only Outcome Model Status copy unless a later sprint approves a narrower replacement

Proposed safe copy direction:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

Unsafe copy direction:

- `87% chance`
- `High probability`
- `Green band`
- `Model favorite`
- `Top outcome`
- `Sort by outcome`

## 11. QA Checks Before App Wiring Can Be Proposed

A later sprint must pass these QA checks before app wiring can be proposed:

- exact display percentages absent from all artifacts
- coarse display bands absent unless explicitly approved
- no app-readable output exists before schema approval
- no hidden sort key exists
- no rankings/sorting integration exists
- no player-card or table column consumes local-only model output
- no current-player inference has run unless separately approved
- no rookie files or rookie scoring path touched
- no `data/` or `local_exports/` commits
- import scan confirms no app loader references Outcome probability artifacts
- output quarantine audit confirms no promoted artifacts
- copy review confirms no fake precision
- human review confirms calibration caveats are preserved

## 12. Phase 8 App-Wiring Prerequisites

A future Phase 8 app-wiring sprint would need to prove all of the following before touching UI code:

1. Phase 7 display contract artifact completed GREEN.
2. HQ explicitly approves app wiring scope.
3. Approved display semantics are non-numeric or otherwise explicitly authorized.
4. Output schema is reviewed and app-readable status is explicitly authorized.
5. Current-player inference is explicitly authorized if any player-level display is proposed.
6. Exact percentages are explicitly authorized if any percentage is proposed.
7. Coarse bands are explicitly authorized if any band is proposed.
8. Sorting/ranking/hidden-key behavior is explicitly blocked or explicitly authorized.
9. Rollback plan is documented.
10. Tests prove no accidental probability, band, ranking, sorting, or hidden-key exposure.

No Phase 8 app-wiring approval exists after 5DE.

## 13. Recommendation

5DE recommendation: GREEN.

A future Phase 7 local-only display-contract artifact sprint may be proposed next. That sprint should create a local-only contract artifact for human review, not app-readable output, and should preserve the recommended first display concept as non-numeric status only.

5DE does not approve app wiring, app-readable outputs, current-player inference, exact percentages, coarse bands, rankings/sorting, hidden sort keys, or promoted artifacts.

## 14. Blocker Confirmations

Still blocked:

- model training
- production model artifacts
- current-player inference
- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable outputs
- app wiring
- rankings/sorting
- hidden sort keys
- promoted artifacts
- rookie files
- `data/` staging or commits
- `local_exports/` staging or commits
- push/deploy

## 15. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `ebf57d3` anchor commit verified
- `git diff --check` passed

No Python files changed in 5DE, so `python -m py_compile`, Ruff, and pytest were not required.
