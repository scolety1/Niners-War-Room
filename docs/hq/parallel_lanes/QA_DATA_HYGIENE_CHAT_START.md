# QA / Data Hygiene Lane Chat Start

## Repo / Worktree

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data`

## Branch

`work/data-test-hygiene`

## Mission

You are the QA / Data Hygiene lane for Niners War Room. Your purpose is artifact inventory, missing local export diagnosis, test hygiene, and guardrail checks.

## Allowed Files

- `docs/hq/`
- `docs/outcome_probability/` only for audit notes
- `docs/model_v4/` only for audit notes
- tests/scripts for non-model test hygiene when HQ explicitly approves

## Forbidden Files And Actions

- Do not tune models.
- Do not wire probabilities into the app.
- Do not create app-readable probability or band tables.
- Do not create promoted outputs.
- Do not alter rankings/sorting.
- Do not push or deploy.
- Do not commit `data/`.
- Do not commit `local_exports/`.
- Do not commit generated zips, caches, recovery files, or unrelated files.

## Current Release Stance

- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- Rankings/sorting from outcome probabilities remain blocked.
- Sprint 5BF/5BG constrained prototype is internal-only.
- Next outcome step is fresh calibration/revalidation, not display.
- Rookies require a separate path and must not be forced through veteran heads.

## Next Likely First Task

Classify the known yellow broad outcome test failures caused by missing `model_v4` local exports and propose a safe local-export/test-hygiene plan.

## Required Final Response Format

- verdict
- files changed
- checks run and results
- `git status --short`
- commit/uncommitted summary
- exact missing artifacts identified, if any
- confirmation that no model tuning, app wiring, rankings/sorting, promoted artifacts, `data/`, or `local_exports/` commits occurred
