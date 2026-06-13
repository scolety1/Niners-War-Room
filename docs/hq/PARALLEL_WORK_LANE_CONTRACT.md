# NWR Parallel Work Lane Contract

## Purpose

This contract defines how parallel Codex agents may work on Niners War Room without stepping on the same working directory, branch, app surface, or model-release gate.

## Core Rules

- One agent per worktree.
- No two agents work in the same working directory.
- No push or deploy unless HQ explicitly approves.
- No app wiring unless HQ explicitly approves.
- No probability display unless the relevant release gate explicitly passes.
- No rankings or sorting changes unless HQ explicitly approves.
- No `data/` commits.
- No `local_exports/` commits.
- No generated zip, cache, temporary export, or recovery artifact commits.
- No promoted model artifacts unless HQ explicitly approves.
- No app-readable probability or band tables unless a release gate explicitly passes.
- All lanes must end with `git status --short`, checks run, files changed, and commit/uncommitted summary.

## Current Release Stance

- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- Rankings and sorting from outcome probabilities remain blocked.
- Sprint 5BF/5BG constrained prototype is internal-only.
- Next outcome step is fresh calibration/revalidation, not display.
- Rookies require a separate path and must not be forced through veteran heads.

## Lane Ownership

### HQ / Master Control

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room`
- Branch: `work/hq-parallel-control`
- Purpose: master control, review, GREEN/YELLOW/RED decisions, integration planning.
- Default posture: review and gatekeeping, not feature coding.

### Outcome Column Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
- Branch: `work/outcome-column-gate`
- Purpose: veteran outcome probability column only.
- Allowed zones:
  - `docs/outcome_probability/`
  - `src/services/nwr_outcome*`
  - outcome probability scripts
  - outcome probability tests
- Forbidden zones/actions:
  - rookie framework files
  - app display wiring
  - rankings/sorting
  - promoted/app-readable probability artifacts

### Rookie Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies`
- Branch: `work/rookie-framework-path`
- Purpose: rookie evidence, model, and path design only.
- Allowed zones:
  - rookie docs
  - rookie services/scripts/tests
  - rookie evidence audits
  - rookie local-only exports
- Forbidden zones/actions:
  - veteran threshold probability services
  - forcing rookies through veteran heads
  - app display wiring
  - rankings/sorting
  - ADP/rankings/projections/market contamination

### QA / Data Hygiene Lane

- Path: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data`
- Branch: `work/data-test-hygiene`
- Purpose: artifact inventory, missing local export diagnosis, test hygiene, guardrail checks.
- Allowed zones:
  - `docs/hq/`
  - `docs/outcome_probability/` only for audit notes
  - `docs/model_v4/` only for audit notes
  - tests/scripts for non-model test hygiene if HQ approves
- Forbidden zones/actions:
  - model tuning
  - app display wiring
  - rankings/sorting
  - promoted outputs

## Final Response Requirements For Every Lane

Every lane must end with:

- branch and worktree path
- files changed
- checks run and results
- `git status --short`
- committed files, if any
- uncommitted files, if any
- confirmation that `data/` was not committed
- confirmation that `local_exports/` was not committed
- confirmation that no app display, probability display, or rankings/sorting changes were made unless HQ explicitly approved them
