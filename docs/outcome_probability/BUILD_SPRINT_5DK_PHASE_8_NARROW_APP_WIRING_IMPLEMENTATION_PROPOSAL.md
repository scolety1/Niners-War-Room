# Sprint 5DK: Phase 8 Narrow App-Wiring Implementation Proposal

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROCEED_TO_STATUS_CONTRACT_QA_FIXTURE_DESIGN`

Sprint type: `DOCS_ONLY_IMPLEMENTATION_PROPOSAL_NO_CODE_TOUCH`

## 1. Scope

Sprint 5DK proposes the narrowest possible future app-wiring implementation for the Outcome Column. This sprint does not edit app UI, service, or source files. It does not create app-readable outputs, current-player inference, current-player probabilities, exact display percentages, coarse display bands, model training, production model artifacts, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Narrow First App-Wiring Concept

The only future implementation concept proposed by 5DK is:

`non_numeric_outcome_status_only`

The future UI may show plain status text only. It must not show or carry a probability, score, band, rank, hidden order value, model confidence value, or player-comparison signal.

## 3. Approved Status Vocabulary

Only these status keys are approved for future implementation planning:

- `internal_review_passed`
- `under_review`
- `unavailable`

Human-facing copy family:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

No other values, labels, icons, color buckets, tiers, or score-like variants are approved.

## 4. Eligible Heads

Eligible heads for future non-numeric status planning only:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution, deferred, blocked, unknown, and unapproved heads must fail closed.

## 5. Blocked Numeric And Inference Policies

Exact percentages remain blocked.

Coarse display bands remain blocked.

Current-player probability inference remains blocked unless a later explicit HQ sprint approves a non-numeric status-only inference path and audits all sources and outputs.

App-readable probability, band, and status artifacts remain blocked in 5DK. A later app-wiring packet would need to explicitly authorize any app-readable status artifact before it is created.

## 6. Future Implementation Approach

A future app-wiring implementation should:

1. preserve existing status-only Outcome Model Status behavior until replacement is approved
2. add only non-numeric status copy if HQ explicitly approves UI edits
3. keep status data separate from ranking, sorting, and scoring flows
4. expose no hidden status priority field
5. expose no model probability, band, score, or rank field
6. render unavailable status gracefully when no approved status is present
7. include tests before committing any UI/source change

The implementation must not affect rankings, sorting, hidden sort keys, downloads, player ordering, model value, private score, or promoted artifacts.

## 7. Candidate UI Placement Options

Candidate placements for future review only:

- small non-numeric text in a player detail/status area
- non-sortable table text column only if HQ explicitly approves a table display
- status-only help tooltip explaining that no probability is released
- existing Outcome Model Status area if it can remain non-numeric and non-sortable

High-risk placements requiring extra caution:

- `app/pages/05_rankings.py`
- player detail cards or panels
- draft board or live draft room surfaces
- downloadable/exportable tables
- ranking or sorting controls

5DK does not edit any of these files.

## 8. Tooltip And Copy Language

Allowed tooltip direction:

`Outcome model status is non-numeric. No probabilities, bands, scores, or ranking effects are shown.`

Forbidden language:

- odds language
- percentages
- high/medium/low labels
- green/yellow/red labels
- model favorite or edge language
- best/top/rank wording
- any phrase implying calibrated player probability

## 9. Future Files That May Need Review

Future app-wiring planning may inspect:

- `app/navigation.py`
- `app/pages/05_rankings.py`
- `app/components/player_detail_card.py`
- `app/components/player_detail_panel.py`
- `app/components/tables.py`
- `src/services/nwr_outcome_status_display_service.py`
- `src/services/table_sort_service.py`
- `src/services/ranking_surface_service.py`
- relevant tests under `tests/`

These files are listed for future review only. 5DK does not edit them.

## 10. Future Tests Required Before UI Source Can Be Touched

Future tests must prove:

- exact status vocabulary only
- no exact percentages
- no coarse bands
- no current-player probabilities
- no probability or band fields
- no ranking or sorting effect
- no hidden sort key
- no promoted artifact usage
- excluded heads fail closed
- unavailable status renders safely
- downloads do not expose Outcome internals

## 11. Rollback Plan For Future Implementation

If a future app-wiring implementation leaks precision or affects ranking/sorting:

1. stop immediately
2. remove the UI/source change
3. remove any app-readable status artifact
4. verify no `data/` or `local_exports/` content was staged
5. rerun no-leakage guard checks
6. document the failure as YELLOW or RED
7. do not proceed to push or deploy

## 12. Recommendation

5DK recommendation: GREEN.

Sprint 5DL may proceed as a docs-only non-numeric status contract and QA fixture design sprint. App/source edits remain blocked.

## 13. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `38b01cd` anchor commit verified
- `git diff --check` passed

No Python files changed in 5DK, so `python -m py_compile`, Ruff, and pytest were not required.
