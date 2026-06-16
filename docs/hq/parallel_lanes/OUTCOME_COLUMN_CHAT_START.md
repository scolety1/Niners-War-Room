# Outcome Column Lane Chat Start

## Repo / Worktree

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`

## Branch

`work/outcome-column-gate`

## Mission

You are the Outcome Column lane for Niners War Room. Your purpose is veteran outcome probability research and release-gate work only.

## Allowed Files

- `docs/outcome_probability/`
- `src/services/nwr_outcome*`
- outcome probability scripts
- outcome probability tests
- sprint-specific local-only exports under unique `local_exports/outcome_probability/...` folders

## Forbidden Files And Actions

- Do not edit rookie framework files.
- Do not wire probabilities into the app.
- Do not create app-readable probability or band tables.
- Do not create promoted model artifacts.
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

Fresh internal calibration/revalidation of the constrained prototype after 5BG. This remains internal-only and must not create display/app artifacts.

## Required Final Response Format

- verdict
- files changed
- local-only exports created, if any
- tests/checks run and results
- `git status --short`
- commit/uncommitted summary
- confirmation that exact probabilities, coarse bands, app wiring, rankings/sorting, promoted artifacts, `data/`, and `local_exports/` commits remain blocked
