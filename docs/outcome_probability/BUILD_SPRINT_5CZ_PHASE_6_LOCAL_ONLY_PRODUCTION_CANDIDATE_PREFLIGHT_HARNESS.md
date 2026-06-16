# Sprint 5CZ: Phase 6 Local-Only Production-Candidate Preflight Harness

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_LOCAL_ONLY_PRODUCTION_CANDIDATE_HARNESS`

Sprint type: `HARNESS_AND_PREFLIGHT_NO_CURRENT_INFERENCE_NO_APP_OUTPUT`

## 1. Scope

Sprint 5CZ created a narrow Phase 6 local-only production-candidate modeling harness and ran a preflight validation. The sprint did not run current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

The harness reuses the committed Phase 5 historical evaluation mechanics, but narrows the allowed heads to the 5CY Phase 6 production-candidate set and writes only quarantined local evidence.

## 2. Files Created

Tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5CZ_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_PREFLIGHT_HARNESS.md`
- `scripts/outcome_probability/build_sprint_5cz_phase6_production_candidate_harness.py`

Local-only preflight evidence:

`local_exports/outcome_probability/sprint_5cz_phase6_production_candidate_harness/`

Local-only files created:

- `metadata_preflight.json`

The local-only evidence is ignored, not app-readable, and not staged or committed.

## 3. Eligible Heads

The harness allows exactly these Phase 6 heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

The harness fails closed if any caution, deferred, blocked, unknown, or unapproved head is requested.

## 4. Excluded Heads

Caution heads excluded from this first production-candidate set:

- `qb_t18`
- `qb_t24`
- `rb_t24`
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

## 5. Harness Design

The harness:

- loads only historical 2010-2019 feature/label packages
- uses completed prior-season source-safe features only
- uses same-season final stats only as historical labels
- uses deterministic rolling historical folds
- compares the low-complexity logistic candidate against base-rate, prior-rank, and prior-PPG baselines
- emits aggregate metrics, feature quarantine audit rows, and coefficient diagnostics only
- emits no row-level or player-facing prediction table
- emits no serialized model object
- emits no app-readable, promoted, rankings, sorting, hidden-key, probability, or band artifact

Approved historical feature allowlist:

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

Forbidden feature terms remain blocked, including fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share fields, ADP, projections, public rankings, consensus, market/trade values, RotoWire values, prior fantasy draft history, legacy `private_score`, same-season target stats as features, and current-player fields.

## 6. Output Quarantine

Allowed output root:

`local_exports/outcome_probability/`

Sprint-specific preflight output:

`local_exports/outcome_probability/sprint_5cz_phase6_production_candidate_harness/`

The harness fails closed if the output path is outside the local outcome export root or contains app, Streamlit, or `data` path components. Output metadata uses `output_scope=internal_only_not_app_readable`.

## 7. Preflight Result

Preflight command run:

`python scripts\outcome_probability\build_sprint_5cz_phase6_production_candidate_harness.py --mode preflight --heads approved --output-dir local_exports\outcome_probability\sprint_5cz_phase6_production_candidate_harness`

Result:

| Check | Result |
| --- | ---: |
| Historical rows loaded | 3801 |
| Approved Phase 6 head count | 6 |
| Sample head checked | `qb_t12` |
| Aggregate dry-run rows generated | 16 |
| Coefficient dry-run rows generated | 48 |
| Current-player inference performed | false |
| App-readable outputs created | false |
| Serialized model artifacts created | false |

## 8. Gate Verdict

5CZ verdict: GREEN.

The harness is local-only, eligible-head-only, historical-only, non-app-readable, deterministic enough for audit, and contains no current-player inference path. Sprint 5DA may run the harness for the eligible Phase 6 heads only.

## 9. Blocker Confirmations

Still blocked:

- current-player inference
- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable probability, band, or status outputs
- app wiring
- rankings/sorting
- hidden sort keys
- promoted artifacts
- rookie files
- `data/` commits
- `local_exports/` commits
- push/deploy

## 10. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- harness preflight passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5cz_phase6_production_candidate_harness.py` passed
- `git diff --check` passed

Ruff and pytest were not required and no package installation was performed.
