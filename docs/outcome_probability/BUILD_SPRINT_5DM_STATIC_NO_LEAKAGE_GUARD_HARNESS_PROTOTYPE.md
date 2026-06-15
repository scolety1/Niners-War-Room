# Sprint 5DM: Static No-Leakage Guard Harness Prototype

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROCEED_TO_CODE_TOUCH_APPROVAL_READINESS`

Sprint type: `DOCS_ONLY_STATIC_GUARD_PROTOTYPE_NO_CODE_TOUCH`

## 1. Scope

Sprint 5DM prototypes the design for a narrow static guard harness that can detect forbidden Outcome display leakage before a future app-wiring sprint. The prototype is documented only. No script was created because this runway remains no-source-edit planning and the optional script is not required to keep the gate GREEN.

This sprint did not edit app UI, service, or source files. It did not create app-readable outputs, JSON/CSV/parquet display artifacts, current-player inference, current-player probabilities, exact display percentages, coarse display bands, model training, production model artifacts, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Guard Purpose

The future static guard should inspect proposed Phase 8 app-wiring changes before commit and fail closed if the implementation leaks numeric or sortable Outcome data.

The guard is intended to run after a future packet has explicit approval to touch app/source files, not during 5DM.

## 3. What The Guard Checks

The future guard should check proposed changed files for:

1. exact percentage syntax in Outcome display context
2. probability-like field names in app/display context
3. coarse-band labels or band fields in app/display context
4. hidden sort-key fields related to Outcome status
5. ranking/sorting logic that references Outcome status
6. app-readable probability or band artifact references
7. app-readable status artifacts not explicitly approved by the future packet
8. status values outside the approved vocabulary
9. head values outside the eligible head list
10. current-player probability inference references
11. promoted artifact path references
12. direct reads from `local_exports/outcome_probability/`

Approved status vocabulary:

- `internal_review_passed`
- `under_review`
- `unavailable`

Eligible heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

## 4. Forbidden Pattern Families

Future guard pattern families:

- exact numeric display: `%`, `probability`, `prob`, `pct`, decimal odds
- band display: `high`, `medium`, `low`, `green`, `yellow`, `red`, `band`
- hidden ordering: `outcome_sort`, `outcome_rank`, `outcome_score`, `outcome_status_priority`, `hidden_outcome_sort_key`
- app artifacts: `outcome_player_probabilities`, `app_probability_table`, `player_probabilities`, `outcome_band`
- current inference: `current_player_probability`, `current_player_inference`, `predict_current`
- promotion: `promoted`, `production_model_artifact`, `release_artifact`

The guard should apply context rules so docs that discuss blocked terms do not automatically fail, but app/source or fixture files using these terms as live fields should fail or return YELLOW.

## 5. What The Guard Intentionally Does Not Check

The guard does not:

- train models
- import app modules
- run Streamlit
- infer current players
- read `data/`
- read `local_exports/`
- write app-readable files
- decide whether display copy is good UX
- replace human review
- approve app wiring

The guard is a static tripwire, not a release gate by itself.

## 6. How A Future Guard Would Run

Future command shape, if HQ later approves a script:

`python scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py --changed-files`

Expected behavior:

- scan only proposed changed app/source/test/fixture files
- print a GREEN/YELLOW/RED result to the terminal
- write no files by default
- return nonzero on RED
- return a clearly reviewable warning on YELLOW

No such script is created by 5DM.

## 7. GREEN / YELLOW / RED Semantics

GREEN:

- only approved vocabulary appears
- no numeric display terms appear in live app/source context
- no bands appear in live app/source context
- no ranking/sorting/hidden-key usage appears
- no app-readable probability or band artifacts appear
- no current-player inference appears

YELLOW:

- the guard cannot classify context safely
- docs or tests include blocked terms in a way that might be legitimate but needs review
- an app-readable status artifact is proposed but its approval is unclear

RED:

- exact percentages, coarse bands, probabilities, rankings, hidden keys, promoted artifacts, or current-player inference appear in a live implementation path
- unapproved heads are wired into display
- app/source files load local-only model evidence directly

## 8. False-Positive Handling

False positives must not be ignored. A future packet should:

1. document why the finding is safe
2. narrow the pattern or add an explicit allowlist only for that context
3. rerun the guard
4. keep the sprint YELLOW if uncertainty remains

## 9. Why The Prototype Creates No App-Readable Output

5DM is a design sprint. It creates no guard output file, no fixture, no JSON/CSV/parquet artifact, no app-readable status file, and no local export. The only tracked artifact is this documentation.

## 10. Why It Does Not Touch App/Source Files

The packet hard line is no app/source edits. The future guard is defined so the next packet can ask for a narrow code-touch approval with an exact file allowlist. 5DM preserves that boundary.

## 11. Recommendation

5DM recommendation: GREEN.

Sprint 5DN may proceed as a Phase 8 code-touch approval readiness verdict. App/source edits remain blocked.

## 12. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `git diff --check` passed

No Python files changed in 5DM, so `python -m py_compile`, Ruff, and pytest were not required.
