# Sprint 5CT: Local-Only Candidate Modeling Preflight And Harness

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_LOCAL_ONLY_HARNESS_PREFLIGHT`

Sprint type: `HARNESS_AND_PREFLIGHT_NO_FULL_EVALUATION_NO_RELEASE`

## 1. Scope

Sprint 5CT created the Phase 5 local-only candidate modeling harness and ran a tiny preflight/dry-run validation. This sprint did not run the full candidate evaluation, create production model artifacts, serialize models, run current-player inference, create current-player probabilities, create app-readable outputs, create exact display percentages, create coarse bands, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

## 2. Files Created

Tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5CT_LOCAL_ONLY_CANDIDATE_MODELING_PREFLIGHT_AND_HARNESS.md`
- `scripts/outcome_probability/run_sprint_5ct_phase5_candidate_modeling_harness.py`

Local-only preflight evidence:

`local_exports/outcome_probability/sprint_5ct_phase5_candidate_modeling_preflight/`

Local-only files created:

- `metadata_preflight.json`

The local-only evidence is not app-readable and is not staged or committed.

## 3. Harness Summary

The harness can:

- load only historical 2010-2019 feature/label rows from approved local packages
- filter to 5CS-approved candidate heads
- exclude deferred and blocked heads by default
- enforce approved source-safe features only
- fail closed on forbidden feature terms
- fail closed on app-readable source rows
- fail closed on current-season/current-player rows
- run deterministic rolling historical folds
- emit aggregate metrics only to a sprint-specific local-only export directory
- avoid serializing or promoting model artifacts

## 4. Candidate Heads Allowed

Allowed candidate heads:

- `qb_t12`
- `qb_t18`
- `qb_t24`
- `rb_t12`
- `rb_t24`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`
- `te_t18`
- `te_t24`

Deferred heads excluded:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads excluded:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

The harness fails closed if any deferred, blocked, unknown, or unapproved head is requested.

## 5. Anti-Leakage Checks

The harness enforces the 5CS/5CT feature allowlist:

- `prior_completed_season_games`
- `prior_completed_season_games_active`
- `prior_completed_season_games_played`
- `prior_completed_season_passing_yards`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_rushing_yards`
- `prior_season_nwr_finish_rank`
- `prior_season_nwr_ppg`

The harness fails closed if a feature contains forbidden terms such as fantasy, EPA, WOPR, RACR, PACR, Dakota, target share, ADP, projection, ranking, market, trade, RotoWire, private score, same-year, or target-year terms.

## 6. Output Quarantine Checks

The harness requires output under:

`local_exports/outcome_probability/`

The harness fails closed if an output path is outside local outcome exports or contains forbidden path components such as app, Streamlit, or data.

The harness does not write:

- row-level/player-level prediction exports
- current-player predictions
- app-readable outputs
- serialized model artifacts
- production model artifacts
- exact display percentages
- coarse display bands
- rankings/sorting outputs
- hidden sort keys
- promoted artifacts

## 7. Dry-Run Result

Preflight command run:

`python scripts\outcome_probability\run_sprint_5ct_phase5_candidate_modeling_harness.py --mode preflight --heads approved --output-dir local_exports\outcome_probability\sprint_5ct_phase5_candidate_modeling_preflight`

Dry-run result:

| Check | Result |
| --- | --- |
| Historical rows loaded | 3801 |
| Approved head count | 11 |
| Sample head checked | `qb_t12` |
| Deferred heads excluded | pass |
| Blocked heads excluded | pass |
| Current-player inference performed | false |
| App-readable outputs created | false |
| Serialized model artifacts created | false |

## 8. Verdict

5CT verdict: GREEN.

The harness exists, is fail-closed, excludes deferred/blocked heads, blocks current-player inference and app-readable outputs, avoids serialized models, and writes only local-only evidence.

5CU is approved to run next using the committed harness.

## 9. Checks

Checks run:

- preflight repo/path/branch/status/log check passed
- harness preflight/dry-run passed
- `python -m py_compile scripts\outcome_probability\run_sprint_5ct_phase5_candidate_modeling_harness.py` passed
- `git diff --check` passed

Ruff and pytest were not required and no package installation was performed.
