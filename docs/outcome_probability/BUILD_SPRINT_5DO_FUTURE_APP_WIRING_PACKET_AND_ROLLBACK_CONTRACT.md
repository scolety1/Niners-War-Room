# Sprint 5DO: Future App-Wiring Packet And Rollback Contract

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_FUTURE_NARROW_APP_WIRING_PACKET_MAY_BE_PREPARED_NEXT`

Sprint type: `DOCS_ONLY_NEXT_PACKET_CONTRACT_NO_APP_EDIT`

## 1. Scope

Sprint 5DO prepares the contract for the next packet that may touch app/source files. This sprint does not touch app/source files. It does not create app-readable outputs, current-player inference, current-player probabilities, exact display percentages, coarse display bands, model training, production model artifacts, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Future Packet Purpose

The exact future packet purpose:

`narrow_non_numeric_outcome_status_display_only`

The future packet may implement only non-numeric Outcome status display if the prompt provides an exact file allowlist and keeps all blockers active.

## 3. Allowed Status Vocabulary

Allowed status keys:

- `internal_review_passed`
- `under_review`
- `unavailable`

Allowed copy:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

No additional vocabulary is allowed unless HQ explicitly updates the contract.

## 4. Eligible Heads

Eligible heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution, deferred, blocked, unknown, and unapproved heads must fail closed.

## 5. Forbidden Outputs

Forbidden outputs:

- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable probability artifacts
- app-readable band artifacts
- model scores
- model ranks
- ranking/sorting effects
- hidden sort keys
- promoted artifacts
- production model artifacts
- serialized production models
- direct app reads from local-only model evidence

If any forbidden output appears, the future packet must stop.

## 6. Future Files That May Be Inspected Or Edited

Future packet may inspect app/source files read-only as needed.

Future packet may edit files only if they are explicitly named by HQ in that packet. Candidate files that may require review include:

- `app/pages/05_rankings.py`
- `app/components/player_detail_card.py`
- `app/components/player_detail_panel.py`
- `app/components/tables.py`
- `src/services/nwr_outcome_status_display_service.py`
- `src/services/table_sort_service.py`
- `src/services/ranking_surface_service.py`
- relevant `tests/` files

5DO does not authorize editing those files by itself. The next packet must provide the exact allowlist before any edit.

## 7. Required Tests Before Future Commit

Future implementation must include tests proving:

- approved vocabulary only
- eligible heads only
- unavailable fallback for missing/malformed status
- no exact percentages
- no coarse bands
- no current-player probabilities
- no probability fields
- no band fields
- no model scores
- no ranking/sorting effects
- no hidden sort keys
- no promoted artifacts
- no app reads from `local_exports/outcome_probability/`
- no `data/` or `local_exports/` staging

Tests must run before any commit in the future packet.

## 8. Required Static No-Leakage Checks

Future packet must run a static no-leakage check, either as a documented command or an approved guard script. The check must inspect changed app/source/test files for:

- probability-like field names
- percentage symbols in Outcome display context
- band-like field names
- ranking/sorting references to Outcome status
- hidden-key field names
- promoted artifact paths
- direct local-only evidence reads
- unapproved status vocabulary
- unapproved head names

YELLOW or RED results must stop the packet.

## 9. Manual QA Checklist

Manual QA must verify:

1. the UI copy is non-numeric
2. the UI copy matches approved vocabulary
3. no color, icon, badge, or tooltip implies model strength
4. Outcome status cannot sort players
5. Outcome status cannot rank players
6. Outcome status is absent from hidden sort/filter state
7. app downloads do not include Outcome internals
8. excluded heads do not display approved status
9. missing status renders unavailable
10. rollback can remove the feature cleanly

## 10. Rollback Plan

If UI status display leaks precision or affects ranking/sorting:

1. stop the sprint
2. do not commit
3. revert only the future packet's app/source edits
4. remove any unauthorized app-readable artifact
5. verify `git status --short`
6. verify `data/` and `local_exports/` were not staged
7. rerun tests and static checks
8. document RED or YELLOW with exact offending files

If the leak is found after a commit in a future packet, rollback must use a forward revert commit unless HQ explicitly instructs otherwise.

## 11. Human-Review Checkpoint Before Push Or Deploy

No push or deploy may occur until:

- human review approves the UI semantics
- human review confirms no fake precision
- tests pass
- static no-leakage checks pass
- HQ explicitly approves push/deploy in a later sprint

Push and deploy remain blocked after 5DO.

## 12. Final Verdict

5DO recommendation: GREEN.

The future narrow Outcome app-wiring implementation packet may be prepared next. It may be allowed to touch app/source files only if the next packet explicitly approves an exact file allowlist and preserves the contract above.

5DO itself does not touch app/source files and does not approve push/deploy.

## 13. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- 5DK/5DL/5DM/5DN review completed
- `git diff --check` passed

No Python files changed in 5DO, so `python -m py_compile`, Ruff, and pytest were not required.
