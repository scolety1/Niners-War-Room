# Sprint 5EJ-R - Player ID Allowlist Amendment

## Purpose

Sprint 5EJ-R amends the Phase 11 numeric Outcome display allowlist after the clean 5EJ stop showed that Rankings rows need `player_id` exposed for the required internal join.

This sprint is allowlist/design only. No app, source, test, artifact, ranking, or sorting behavior was changed.

## Preflight

- Repo path verified: `C:/Users/smcol/Documents/Vacation/Niners-War-Room-outcome`
- Branch verified: `work/outcome-column-gate`
- Recent log includes committed Sprint 5EI: `545656a Create numeric outcome display artifact contract`
- Expected dirty state remains limited to `?? data/`

## Original 5EH Allowlist Summary

The committed Sprint 5EH allowlist approved the following Phase 11 file sets:

- Sprint 5EI artifact/service/generator/test:
  - `docs/outcome_probability/BUILD_SPRINT_5EI_APP_READABLE_NUMERIC_ARTIFACT_CONTRACT_AND_GENERATOR.md`
  - `src/services/nwr_outcome_numeric_probability_display_service.py`
  - `scripts/outcome_probability/build_phase11_numeric_outcome_display_artifact_v1.py`
  - `app/generated/outcome_probability/numeric_outcome_display_v1.csv`
  - `tests/test_nwr_outcome_numeric_probability_display_service.py`
- Sprint 5EJ narrow Rankings wiring:
  - `docs/outcome_probability/BUILD_SPRINT_5EJ_NARROW_DISPLAY_ONLY_RANKINGS_PAGE_NUMERIC_OUTCOME_WIRING.md`
  - `app/pages/05_rankings.py`
  - `tests/test_dynasty_rankings_page.py`
- Sprint 5EK tests/guards:
  - `docs/outcome_probability/BUILD_SPRINT_5EK_NUMERIC_DISPLAY_TESTS_AND_NO_LEAKAGE_GUARDS.md`
  - `tests/test_nwr_outcome_numeric_probability_display_service.py`
  - `tests/test_dynasty_rankings_page.py`
  - `scripts/outcome_probability/audit_phase11_numeric_outcome_display_static_guard_v1.py`
- Sprint 5EL audit:
  - `docs/outcome_probability/BUILD_SPRINT_5EL_NUMERIC_DISPLAY_STATIC_AUDIT_AND_HUMAN_REVIEW_SAMPLE.md`
- Sprint 5EM readiness verdict:
  - `docs/outcome_probability/BUILD_SPRINT_5EM_NUMERIC_OUTCOME_APP_DISPLAY_READINESS_VERDICT.md`

The original allowlist also established `player_id` as the required stable join key and blocked name-based joins, sorting/ranking effects, hidden sort keys, unapproved heads, promoted artifacts, `data/` commits, and `local_exports/` commits.

## Stop Finding

Sprint 5EJ stopped correctly because:

- The numeric Outcome display must join Rankings rows to the app-readable artifact by `player_id` only.
- `app/pages/05_rankings.py` receives rows from `build_player_board_score_rows(...)`.
- `src/services/player_board_score_service.py` uses `player_id` internally to build those rows, but the returned dictionaries do not expose `player_id`.
- Joining by player name, display label, team, or position would violate the Phase 11 contract.
- Editing `src/services/player_board_score_service.py` was not included in the original 5EH allowlist.

## Additional File Required

The minimum additional file required for 5EJ-R2 is:

- `src/services/player_board_score_service.py`

Reason: this is the narrow source of the Rankings page row dictionaries and can expose the existing internal `player_id` as an internal-only join key without creating model output, probability output, ranking behavior, sorting behavior, or a promoted artifact.

No additional source/UI files beyond the amended list below are required by the current repair plan.

## Amended Exact 5EJ-R2 Allowlist

Sprint 5EJ-R2 may touch only:

- `docs/outcome_probability/BUILD_SPRINT_5EJ_R2_NARROW_PLAYER_ID_JOIN_NUMERIC_DISPLAY_WIRING.md`
- `src/services/player_board_score_service.py`
- `app/pages/05_rankings.py`
- `tests/test_dynasty_rankings_page.py`
- `tests/test_nwr_outcome_numeric_probability_display_service.py`

Sprint 5EJ-R2 may consume but should not rewrite the committed 5EI artifact unless a later gate explicitly requires a generator refresh:

- `app/generated/outcome_probability/numeric_outcome_display_v1.csv`

Sprint 5EJ-R2 may use the already committed numeric display service but should not need to edit it:

- `src/services/nwr_outcome_numeric_probability_display_service.py`

If 5EJ-R2 needs any additional app page, component, service, ranking pipeline, sorting pipeline, generated artifact, or test outside this amended allowlist, the sprint must stop and report YELLOW.

## Internal Join Key Policy

- `player_id` may be exposed in in-memory Rankings row dictionaries only as an internal join key.
- `player_id` must not become a visible Rankings column.
- `player_id` must not become a hidden sort key.
- Numeric Outcome display values must not affect NWR rank, private score, league rank movement, default sort, or any ranking/sorting behavior.
- Name-based joins remain forbidden.

## Boundaries Preserved

- No code behavior changed in this sprint.
- No Top 6 or unapproved heads were displayed or emitted.
- No current-player inference was run.
- No model training was run.
- No sorting, ranking, hidden key, or promoted artifact path was created.
- `data/` and `local_exports/` remain uncommitted.
- No rookie files were touched.
- No push, deploy, release, merge, or main push occurred.

## Verdict

GREEN for 5EJ-R2 to proceed using the amended exact allowlist above.
