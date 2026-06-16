# Sprint 5DI: Non-Numeric Status QA Contract And Test Plan

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROCEED_TO_PHASE_8_READINESS_VERDICT`

Sprint type: `DOCS_ONLY_QA_CONTRACT_NO_APP_EDIT`

## 1. Scope

Sprint 5DI defines a QA/test contract for a future app-wiring sprint that may eventually show only safe non-numeric Outcome status language. This sprint does not implement tests, edit app/source files, create app-readable outputs, create current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, change rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, stage or commit `data/`, stage or commit `local_exports/`, push, deploy, use internet lookup, or install packages.

## 2. Approved Vocabulary Under Test

Only these status keys may be tested for a future display path:

- `internal_review_passed`
- `under_review`
- `unavailable`

Only these copy forms may be considered:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

No other status values, labels, or implied tiers are approved.

## 3. Eligible And Excluded Head Tests

Eligible planning heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Required tests:

- eligible heads can be recognized by the display contract
- caution heads return unavailable or fail closed
- deferred heads return unavailable or fail closed
- blocked heads return unavailable or fail closed
- unknown heads return unavailable or fail closed
- app-visible copy never exposes internal head names unless HQ explicitly approves technical-review text

Excluded heads:

- caution: `qb_t18`, `qb_t24`, `rb_t24`, `te_t18`, `te_t24`
- deferred: `rb_t36`, `rb_t48`, `wr_t48`
- blocked: `qb_t6`, `rb_t6`, `wr_t6`, `te_t3`, `te_t6`

## 4. Non-Numeric Status Acceptance Tests

Future tests must prove:

1. rendered status text matches the approved vocabulary exactly
2. no numeric value appears in the Outcome status cell
3. no percentage symbol appears in the Outcome status cell
4. no decimal probability appears in the Outcome status cell
5. no odds language appears in the Outcome status cell
6. no color ramp, badge tier, or score-like label is introduced
7. unavailable rows render gracefully without errors
8. missing status rows render as `Outcome model: unavailable`
9. unsupported positions render as unavailable or not applicable according to the approved contract
10. no status display is used as a player-comparison signal

## 5. Exact Percentage Blocker Tests

Future tests must fail if any of these appear in app-visible output, app state, exported tables, fixtures, or loader rows:

- `%`
- `prob`
- `probability`
- `percentage`
- `pct`
- decimal probability values
- `top_6_prob`, `top_12_prob`, `top_24_prob`, `top_36_prob`, or similar columns
- any current-player probability field

Exact display percentages remain blocked.

## 6. Coarse Band Blocker Tests

Future tests must fail if Outcome display uses:

- `High`
- `Medium`
- `Low`
- `Green`
- `Yellow`
- `Red`
- `A/B/C`
- numbered buckets
- band ids
- hidden band ranks

Coarse display bands remain blocked.

## 7. Current-Player Probability Blocker Tests

Future tests must prove:

- no current-player inference script runs during app startup
- no current-player probability file is loaded
- no current-player probability field is present in app rows
- no local-only Phase 6 modeling output is loaded by the app
- no `local_exports/outcome_probability/` path is imported by app code
- no outcome model artifact is loaded by app code

Current-player probabilities remain blocked.

## 8. Sorting, Ranking, And Hidden-Key Tests

Future tests must prove:

- Outcome status is not a sortable table column
- Outcome status is not a filter option unless HQ explicitly approves a non-ranking filter
- no `outcome_sort`, `outcome_rank`, `outcome_status_priority`, `outcome_score`, or `hidden_outcome_sort_key` field exists
- table sort specs do not reference Outcome status
- ranking surfaces do not read Outcome status
- player detail cards do not include hidden model values
- downloads do not include hidden model values

Rankings/sorting and hidden sort keys remain blocked.

## 9. Promoted Artifact Tests

Future tests must prove:

- no promoted artifact path is written
- no production model artifact is loaded
- no release-service artifact is created
- no `data/` artifact is generated or staged
- no `local_exports/` artifact is committed
- app-readable status files are absent unless the future app-wiring packet explicitly approves them

Promoted artifacts remain blocked.

## 10. Graceful Unavailable Handling

Required unavailable behavior:

- missing player status returns `Outcome model: unavailable`
- excluded head returns unavailable or fails closed before rendering
- unknown position returns unavailable or not applicable
- missing app-readable status source does not crash the page
- status absence cannot trigger fallback numeric display
- status absence cannot trigger hidden sorting or ranking fallback

## 11. Manual Review Checklist

Manual review must confirm:

1. approved vocabulary appears exactly
2. copy remains non-predictive and non-numeric
3. no color or icon implies probability strength
4. no player can be sorted by Outcome status
5. no player can be ranked by Outcome status
6. no hidden status priority exists
7. no current-player probability source was loaded
8. excluded heads are absent or unavailable
9. app downloads do not include Outcome internals
10. `data/` and `local_exports/` remain uncommitted

## 12. Required Evidence Before UI Code Sprint

Before any UI code sprint can be proposed, HQ must have:

- GREEN 5DH static inventory
- GREEN 5DI QA contract
- GREEN 5DJ readiness verdict
- explicit app-wiring packet approval
- exact file allowlist for source edits
- tests to be created or updated
- rollback plan
- proof that app-readable output scope is approved or intentionally absent
- proof that numeric display, ranking, sorting, hidden keys, and promoted artifacts remain blocked

## 13. Recommendation

5DI recommendation: GREEN.

A Phase 8 readiness verdict sprint may proceed next. App wiring remains blocked.

## 14. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `git diff --check` passed

No Python files changed in 5DI, so `python -m py_compile`, Ruff, and pytest were not required.
