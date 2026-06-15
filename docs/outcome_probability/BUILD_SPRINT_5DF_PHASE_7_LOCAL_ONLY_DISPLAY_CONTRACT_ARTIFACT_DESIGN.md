# Sprint 5DF: Phase 7 Local-Only Display Contract Artifact Design

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROPOSE_PHASE_8_PLANNING_ONLY`

Sprint type: `DOCS_ONLY_DISPLAY_CONTRACT_DESIGN_NO_APP_SCHEMA_NO_OUTPUT`

## 1. Scope

Sprint 5DF defines a human-readable local-only display contract artifact design for a future Outcome Column. The design is intentionally non-app-consumable and non-numeric. It describes allowed language, status rules, QA gates, blocked paths, and future app-wiring prerequisites.

This sprint did not create app-readable outputs, JSON/CSV/parquet display artifacts, current-player inference, current-player probabilities, exact display percentages, coarse display bands, model training, production model artifacts, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, or package installs.

No script was created. No local-only export was created.

## 2. Inputs Reviewed

5DF starts from:

- `docs/outcome_probability/BUILD_SPRINT_5DE_PHASE_7_OUTCOME_DISPLAY_CONTRACT_PLANNING.md`
- last completed commit `2309367 Plan Phase 7 outcome display contract`

5DE approved a future local-only display-contract artifact sprint to be proposed next. App wiring and numeric display remain blocked.

## 3. First Allowed Display Concept

First allowed display concept:

`non_numeric_status_only`

The Outcome Column may eventually show only a plain-language model-status message. It must not expose odds, probabilities, bands, scores, rankings, hidden sort values, or player-comparison semantics.

Approved concept examples:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

These examples are display-language planning only. 5DF does not create an app-readable schema or output file.

## 4. Approved Status Vocabulary

Approved status vocabulary:

| Status key | Human-readable copy | Meaning |
| --- | --- | --- |
| `internal_review_passed` | `Outcome model: internal review passed` | The player belongs to a future eligible head context where internal model evidence and human review have passed the non-numeric display contract. |
| `under_review` | `Outcome model: under review` | The relevant model/head/display context has not completed all required display-contract and human-review gates. |
| `unavailable` | `Outcome model: unavailable` | No approved non-numeric status is available for this player/context, or the player is outside eligible display scope. |

No other status vocabulary is approved by 5DF.

## 5. Status Usage Rules

`internal_review_passed` may be used only when all of these are true:

- the status belongs to one of the accepted display-planning heads
- a later display-contract artifact sprint has completed GREEN
- human review has signed off on the exact copy
- app-readable output has been separately authorized by HQ
- app wiring has been separately authorized by HQ
- the status is not used for sorting, ranking, filtering, hidden keys, or player comparison

`under_review` may be used only when:

- a head/context is potentially eligible but has not completed all display-contract gates
- the copy does not imply probability, ranking, or a future approval guarantee
- no numeric or band field is exposed

`unavailable` may be used when:

- the player/context is outside the accepted head list
- the head is caution, deferred, blocked, unknown, or not evaluated
- the player/context has not passed required future app wiring QA
- no approved display contract exists

5DF does not authorize any of these statuses to be emitted in an app-readable file or rendered in the app.

## 6. Eligible Display Heads

Only these heads may be considered by a future display-contract implementation path:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Eligibility is limited to non-numeric status planning. It does not approve current-player inference, probabilities, bands, app-readable outputs, app wiring, rankings/sorting, hidden sort keys, or promoted artifacts.

## 7. Excluded Head Policy

Caution heads remain excluded because their Phase 5 evidence required additional calibration review before any production-candidate inclusion:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Deferred heads remain deferred because they were not accepted into the Phase 6 production-candidate set:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads remain blocked because they were not evaluated or remain outside approved support/display gates:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

Any future sprint must fail closed if it attempts to display or app-wire any caution, deferred, blocked, unknown, or unapproved head.

## 8. Copy And UX Guardrails

Required guardrails:

- use status language, not prediction language
- do not display percentages, decimals, odds, rankings, scores, tiers, or bands
- do not expose internal head names to users
- do not use colors that imply a probability gradient
- do not make the status sortable or filterable
- do not include hidden status priority values
- do not include hidden probabilities in DOM, app state, downloads, or caches
- do not compare players by Outcome status
- do not use language such as `high`, `low`, `likely`, `safe`, `lock`, `favorite`, `edge`, `best`, or `top`
- preserve calibration caveats in internal docs and human review

Approved copy must remain bland on purpose. The status can say whether review has passed, not how strong the model believes the player is.

## 9. Exact Percentage Policy

Exact percentages remain blocked.

Forbidden examples:

- `87%`
- `0.87`
- `87 percent`
- `probability=0.87`
- hidden `outcome_probability` fields
- downloadable probability columns

No future app-wiring sprint may add exact percentages unless HQ explicitly approves exact numeric display in a separate sprint.

## 10. Coarse Band Policy

Coarse display bands remain blocked.

Forbidden examples:

- `High`
- `Medium`
- `Low`
- `Green`
- `Yellow`
- `Red`
- `A/B/C`
- bucket ids
- hidden band ranks

Bands may be discussed only as a future gated option. They must not be generated, serialized, made app-readable, or wired into the app without explicit HQ approval.

## 11. Current-Player Probability Policy

Current-player probability outputs remain blocked.

5DF does not approve current-player inference. A future sprint must separately authorize any current-player run, define source inputs, prove no rookie contamination, and audit all outputs before app wiring can be proposed.

## 12. App-Readable Output Policy

App-readable probability, band, and status outputs remain blocked.

5DF does not approve:

- JSON display artifacts
- CSV display artifacts
- parquet display artifacts
- app loader inputs
- Streamlit/player-card fields
- service outputs
- release artifacts
- downloadable tables
- cached app state

This sprint defines only a human-readable design document.

## 13. Rankings, Sorting, Hidden Keys, And Promotion Policy

Rankings/sorting remain blocked.

Hidden sort keys remain blocked.

Promoted artifacts remain blocked.

The status may not be used to order, rank, filter, bucket, prioritize, color-ramp, or score players. No hidden field may be added to recover a model ordering behind a non-numeric UI label.

## 14. QA Tests Required Before App Wiring Can Be Proposed

A future app-wiring proposal must define tests proving:

- no exact percentage fields exist
- no coarse band fields exist
- no hidden sort keys exist
- no model-score fields exist
- no ranking or sorting integration exists
- no current-player probability output exists unless separately approved
- no app loader imports local-only export paths
- no production/promoted artifact path is written
- no rookie files are touched
- only approved status copy appears
- only eligible heads are in scope
- excluded heads fail closed
- app-visible text matches the approved vocabulary exactly
- downloadable/exported data does not include model internals
- `data/` and `local_exports/` remain uncommitted

## 15. Future Phase 8 App-Wiring Prerequisites

Before any Phase 8 sprint touches UI code, it must prove:

1. HQ explicitly approves Phase 8 app wiring.
2. A GREEN display-contract artifact exists.
3. The exact app-readable status schema is approved.
4. The file path for app-readable status output is approved.
5. Current-player inference is approved if any player-context status requires it.
6. Exact percentages remain absent unless separately approved.
7. Coarse bands remain absent unless separately approved.
8. Rankings/sorting and hidden sort keys remain absent unless separately approved.
9. Rollback and kill-switch behavior is documented.
10. Tests cover app import, player-card rendering, downloads, sorting, filtering, and hidden state.

No Phase 8 app-wiring approval exists after 5DF.

## 16. Files A Later App-Wiring Sprint Could Request

A later HQ-approved app-wiring sprint could request files such as:

- a tracked app component or view file
- a tracked app loader or service file
- a tracked test file proving no numeric or hidden output exposure
- a separately approved app-readable status fixture or generated artifact

5DF does not create any of those files. This section is a future planning placeholder, not authorization.

## 17. Recommendation

5DF recommendation: GREEN.

A future Phase 8 planning sprint may be proposed next. It should remain planning-only unless HQ explicitly approves app-wiring implementation. The recommended path is to plan the app integration contract and QA gates before touching UI code.

5DF does not approve app-readable output, current-player inference, current-player probabilities, exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, or promoted artifacts.

## 18. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `2309367` anchor commit verified
- `git diff --check` passed

No Python files changed in 5DF, so `python -m py_compile`, Ruff, and pytest were not required.
