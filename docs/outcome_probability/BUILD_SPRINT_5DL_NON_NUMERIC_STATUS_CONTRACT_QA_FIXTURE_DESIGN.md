# Sprint 5DL: Non-Numeric Status Contract And QA Fixture Design

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROCEED_TO_STATIC_NO_LEAKAGE_GUARD_PROTOTYPE`

Sprint type: `DOCS_ONLY_CONTRACT_FIXTURE_DESIGN_NO_APP_ARTIFACT`

## 1. Scope

Sprint 5DL designs the future non-numeric Outcome status contract and QA fixture strategy. This sprint does not create app-readable JSON, CSV, or parquet files. It does not edit app UI, service, or source files. It does not create app-readable outputs, current-player inference, current-player probabilities, exact display percentages, coarse display bands, model training, production model artifacts, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Human-Readable Local-Only Contract

Future status-contract fixtures should be human-readable review examples first. They must remain local-only and non-production until a later HQ sprint explicitly approves an app-readable status artifact.

5DL does not create fixture files. It defines what a future fixture would need to prove.

## 3. Exact Status Vocabulary

Approved status keys:

- `internal_review_passed`
- `under_review`
- `unavailable`

Approved human-facing copy:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

Any other status value, label, band, color tier, score-like term, or probability-like term must fail QA.

## 4. Status Usage Rules

`internal_review_passed` can be used only when:

- the row is in an eligible head context
- the future app-wiring packet has explicit HQ approval
- the future app-readable status source, if any, is approved
- human review has approved the exact copy
- no numeric, band, ranking, sorting, hidden-key, or probability field is present

`under_review` can be used only when:

- the context is potentially eligible but not approved for internal-review-passed copy
- copy does not imply odds, probability, ranking, or future approval
- no hidden ordinal value exists

`unavailable` must be used or fail closed when:

- the row is outside eligible heads
- the head is caution, deferred, blocked, unknown, or unapproved
- status input is missing or malformed
- status provenance is unavailable
- no approved display contract exists

## 5. Eligible Heads

Eligible heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

All other heads must be treated as unavailable or fail closed.

## 6. Future Fixture Strategy

Future fixtures may demonstrate:

- eligible status renders approved copy
- unavailable status renders approved unavailable copy
- missing status falls back to unavailable
- malformed status fails closed
- caution/deferred/blocked heads are rejected
- numeric strings are rejected
- probability fields are rejected
- band fields are rejected
- sort-key fields are rejected

Future fixtures must remain test fixtures only. They must not become production artifacts, promoted artifacts, or app-readable outputs unless HQ explicitly approves that in a later app-wiring packet.

## 7. No Numeric Fixture Rule

Fixtures must not include:

- player-level probabilities
- exact percentages
- decimal probabilities
- odds
- coarse bands
- model scores
- model ranks
- hidden status priority
- hidden sort keys

Forbidden fields include:

- `outcome_probability`
- `outcome_prob`
- `outcome_pct`
- `outcome_band`
- `outcome_score`
- `outcome_rank`
- `outcome_sort`
- `outcome_status_priority`
- `hidden_outcome_sort_key`

## 8. Negative QA Cases

Negative cases must fail if any future fixture or app row contains:

- `%`
- probability-like fields
- band-like fields
- score-like fields
- rank-like fields
- sort-like fields
- status values outside the approved vocabulary
- unapproved head values
- current-player probability references
- app-readable probability or band artifact references

If a future test cannot classify a value safely, it should return YELLOW or fail closed.

## 9. QA Scenarios

Required QA scenarios:

- eligible head with `internal_review_passed`
- eligible head with `under_review`
- eligible head with `unavailable`
- missing status
- malformed status
- unsupported position
- caution head
- deferred head
- blocked head
- unknown head
- numeric copy injection
- percentage-sign injection
- coarse-band injection
- hidden-sort-key injection
- app-readable probability field injection

## 10. Future Test Locations

If later approved, tests may live under:

- `tests/test_nwr_outcome_status_display_service.py`
- `tests/test_outcome_column_integration_contract.py`
- a new narrow Phase 8 test file under `tests/`

No tests are created by 5DL.

## 11. Forbidden Files And Directories

Still forbidden:

- `data/`
- `local_exports/`
- app/source files
- JSON/CSV/parquet display artifacts
- app-readable probability artifacts
- app-readable band artifacts
- promoted artifact paths
- ranking/sorting pipeline paths
- rookie files

## 12. Recommendation

5DL recommendation: GREEN.

Sprint 5DM may proceed as a static no-leakage guard harness prototype/design sprint. App/source edits remain blocked.

## 13. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `git diff --check` passed

No Python files changed in 5DL, so `python -m py_compile`, Ruff, and pytest were not required.
