# Sprint 5EH - Exact Numeric App Display File Allowlist Discovery

## Purpose

Sprint 5EH discovers the exact files needed for a narrow display-only numeric Outcome probability implementation on the Rankings page. This sprint is discovery and planning only.

No app/source/test files were edited in this sprint. No app-readable artifact was created. No current-player inference was run. No sorting/ranking path was changed. No hidden sort key, promoted artifact, push, deploy, release, merge, or main push occurred.

## Current State Confirmed

- Phase 10 completed GREEN through Sprint 5EG.
- Last completed Phase 10 commit: `c27b705 Record numeric outcome display readiness verdict`.
- Branch: `work/outcome-column-gate`.
- Expected dirty state remains `?? data/`.
- Target display heads:
  - `qb_t12`
  - `rb_t12`
  - `rb_t24`
  - `wr_t12`
  - `wr_t24`
  - `wr_t36`
  - `te_t12`

## Rankings Page Pool And Join Key

Rankings page file:

- `app/pages/05_rankings.py`

The Rankings page builds `formula_rows` through `_load_formula_board(...)`, which calls:

- `src/services/player_board_score_service.py::build_player_board_score_rows`

The Phase 10 discovery established `player_id` as the stable join key. This remains the required join key for Phase 11.

## Minimal Future File Allowlist

The following files are approved for future Phase 11 sprints if each gate remains GREEN.

### 5EI App-Readable Artifact Contract And Generator

Allowed files:

- `docs/outcome_probability/BUILD_SPRINT_5EI_APP_READABLE_NUMERIC_ARTIFACT_CONTRACT_AND_GENERATOR.md`
- `src/services/nwr_outcome_numeric_probability_display_service.py`
- `scripts/outcome_probability/build_phase11_numeric_outcome_display_artifact_v1.py`
- `app/generated/outcome_probability/numeric_outcome_display_v1.csv`
- `tests/test_nwr_outcome_numeric_probability_display_service.py`

Approved app-readable artifact path:

- `app/generated/outcome_probability/numeric_outcome_display_v1.csv`

This is the only approved app-readable numeric Outcome artifact path in Phase 11.

### 5EJ Narrow Rankings Page UI Wiring

Allowed files:

- `docs/outcome_probability/BUILD_SPRINT_5EJ_NARROW_DISPLAY_ONLY_RANKINGS_PAGE_NUMERIC_OUTCOME_WIRING.md`
- `app/pages/05_rankings.py`
- `tests/test_dynasty_rankings_page.py`

### 5EK Numeric Display Tests And Guards

Allowed files:

- `docs/outcome_probability/BUILD_SPRINT_5EK_NUMERIC_DISPLAY_TESTS_AND_NO_LEAKAGE_GUARDS.md`
- `tests/test_nwr_outcome_numeric_probability_display_service.py`
- `tests/test_dynasty_rankings_page.py`
- `scripts/outcome_probability/audit_phase11_numeric_outcome_display_static_guard_v1.py`

### 5EL Static Audit And Human Review Sample

Allowed files:

- `docs/outcome_probability/BUILD_SPRINT_5EL_NUMERIC_DISPLAY_STATIC_AUDIT_AND_HUMAN_REVIEW_SAMPLE.md`

If a code audit helper becomes necessary, the sprint must stop unless HQ approves an expanded allowlist.

### 5EM Final Readiness Verdict

Allowed files:

- `docs/outcome_probability/BUILD_SPRINT_5EM_NUMERIC_OUTCOME_APP_DISPLAY_READINESS_VERDICT.md`

## Display Contract Boundaries

The app-readable artifact must:

- use `player_id` as the join key;
- contain only approved heads;
- use display-safe whole-number percentage strings or unavailable text;
- contain no raw decimal probability fields;
- contain no Top 6 heads;
- contain no unapproved, caution, deferred, or blocked heads;
- contain no sorting/ranking fields;
- contain no hidden keys;
- contain no market/ranking/projection/ADP/trade fields;
- remain inside the approved artifact path.

## Forbidden Files And Directories

Forbidden throughout Phase 11:

- `data/`
- `local_exports/` commits
- rookie files and rookie repo
- unallowlisted app pages/components
- unallowlisted services
- unallowlisted tests
- ranking/sorting pipelines
- hidden sort key files or fields
- promoted artifacts outside `app/generated/outcome_probability/numeric_outcome_display_v1.csv`
- push/deploy/release/merge/main push

## Sorting And Ranking Policy

Outcome numeric display values must not affect ranking order. The Rankings page may display approved percentage text, but the existing rank calculation and `nwr_rank` order must remain unchanged.

No hidden sortable Outcome values may be introduced. The future static guard must scan for Outcome-derived sort/rank/key fields and fail closed.

## Blocked Heads

Top 6 and unapproved heads remain blocked:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

No future Phase 11 file may emit or display these heads.

## Recommendation

Verdict: GREEN for Sprint 5EI.

Sprint 5EI may create the approved app-readable artifact contract/generator using only the allowlisted files above, provided it emits only the seven approved heads, preserves the Phase 10 row universe unless a clearly explained app-pool change exists, and creates no sorting/ranking/hidden-key leakage.
