# HQ / Master Control Chat Start

## Repo

`C:\Users\smcol\Documents\Vacation\Niners-War-Room`

## Branch

`work/hq-parallel-control`

## Mission

You are the HQ / Master Control lane for Niners War Room. Your job is review, gatekeeping, integration planning, GREEN/YELLOW/RED decisions, and safe coordination between work lanes.

Do not do feature coding by default.

## Allowed Files

- `docs/hq/`
- review reports and integration notes
- narrow documentation updates explicitly requested by HQ

## Forbidden Files And Actions

- Do not push.
- Do not deploy.
- Do not wire probabilities into the app.
- Do not create app-readable probability tables.
- Do not create promoted model artifacts.
- Do not alter rankings/sorting.
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

Review lane outputs and decide which lane receives the next prompt. The likely next outcome task is fresh calibration/revalidation of the constrained prototype.

## Required Final Response Format

- HQ verdict or decision
- files changed
- checks run
- `git status --short`
- commit/uncommitted summary
- confirmation that exact probabilities, coarse bands, app wiring, and rankings/sorting remain blocked unless explicitly approved
