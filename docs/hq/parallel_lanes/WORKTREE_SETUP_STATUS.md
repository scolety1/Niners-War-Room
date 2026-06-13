# NWR Parallel Worktree Setup Status

## Setup Intent

This file records the planned lane layout for parallel Niners War Room work. The actual creation results are reported by the setup run final response.

## HQ Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room`
- Branch: `work/hq-parallel-control`
- Status at doc creation: active setup branch

## Outcome Column Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
- Branch: `work/outcome-column-gate`
- Status at doc creation: pending worktree creation

## Rookie Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies`
- Branch: `work/rookie-framework-path`
- Status at doc creation: pending worktree creation

## QA / Data Hygiene Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data`
- Branch: `work/data-test-hygiene`
- Status at doc creation: pending worktree creation

## Optional Local-Only Junction Plan

If safe and supported, each lane worktree may receive local-only directory junctions:

- `local_exports` pointing to `C:\Users\smcol\Documents\Vacation\Niners-War-Room\local_exports`
- `data` pointing to `C:\Users\smcol\Documents\Vacation\Niners-War-Room\data`

These junctions must not be staged or committed. Lanes may read shared local-only data, but must not mutate shared source data. Lane outputs must go to unique sprint-specific local export folders.

## Guardrails

- Do not push.
- Do not deploy.
- Do not commit `data/`.
- Do not commit `local_exports/`.
- Do not commit generated zips, caches, recovery files, or unrelated files.
- Do not wire probabilities into the app.
- Do not create app-readable probability or band tables.
- Do not create promoted model artifacts.
- Do not change rankings/sorting.
