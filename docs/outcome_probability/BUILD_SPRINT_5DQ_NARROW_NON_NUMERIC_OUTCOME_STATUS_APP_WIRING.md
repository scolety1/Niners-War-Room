# Sprint 5DQ: Narrow Non-Numeric Outcome Status App Wiring

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_NARROW_SOURCE_CONTRACT_WIRING`

Sprint type: `NARROW_SOURCE_CONTRACT_NO_UI_PAGE_EDIT_NO_APP_OUTPUT`

## 1. Scope

Sprint 5DQ implements the first narrow Phase 8 code-touch step inside the committed 5DP allowlist. It creates a source-level non-numeric Outcome status contract service. It does not edit UI pages or components, does not create app-readable data artifacts, and does not infer status for current players.

This sprint did not create current-player inference, current-player probabilities, exact display percentages, coarse display bands, app-readable generated outputs, model training, production model artifacts, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Files Changed

Tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5DQ_NARROW_NON_NUMERIC_OUTCOME_STATUS_APP_WIRING.md`
- `src/services/nwr_outcome_phase8_status_contract_service.py`

Both files are within the 5DP allowlist.

## 3. Status Vocabulary Implemented

Implemented status keys:

- `internal_review_passed`
- `under_review`
- `unavailable`

Implemented copy:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

No other status vocabulary is accepted.

## 4. Eligible Heads Enforced

Eligible heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Excluded heads are represented with an unavailable policy and are not eligible for approved status display.

## 5. Fallback Behavior

Default behavior:

- missing status becomes `unavailable`
- unknown status becomes `unavailable`
- unsupported head becomes `unavailable`

Strict mode:

- unsupported status raises `ValueError`
- unsupported head raises `ValueError`

This fails closed and avoids fake confidence.

## 6. Output And Data Boundaries

The new service:

- reads no files
- writes no files
- imports no app modules
- imports no model artifact modules
- does not touch `data/`
- does not touch `local_exports/`
- creates no app-readable output
- creates no generated JSON/CSV/parquet file
- creates no current-player inference

## 7. Ranking, Ordering, And Hidden-Key Boundary

The new service exposes text contract objects only. It does not expose any field intended for player ordering, player comparison, table ordering, hidden weighting, or model value. It does not integrate with ranking or table services.

## 8. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- 5DP allowlist reviewed
- `python -m py_compile src\services\nwr_outcome_phase8_status_contract_service.py` passed
- static review of changed source for forbidden live fields passed
- `git diff --check` passed

Ruff and pytest were not required in 5DQ. Full status-contract tests are reserved for 5DR under the committed allowlist.
