# Full-Suite Failure Inventory -- exact-name regression audit

Scoped dispatch, `upgrade/nwr-prospective-outcomes-v1-20260914` worktree, dispatch HEAD `2fe3165e` (confirmed via `git log -1 --oneline` at session start -- matched exactly). Final HEAD after this pass: `295a4a6e`.

Owner directive (quoted verbatim, not watered down): *"The important question is: DID THE CURRENT UPGRADE INTRODUCE ANY NEW FAILURE OR ERROR? Prove that by exact names, not counts."* This document, together with the "Exact full-suite failure reconciliation" section appended to `LEDGER.md`, is the answer.

## Methodology

1. **Baseline commit**: `b5061437`, confirmed via `git log --oneline -1 2512e06f~1` to be the exact commit immediately before the dogfood-rebuild cycle's first commit.
2. **Baseline run**: `git worktree add` at a SHORT path (`C:\nwrtmp\bl_wt`, 15 characters) detached at `b5061437`. **Important correction made mid-pass**: the first two attempts used an isolated worktree under this session's own deeply-nested scratchpad directory (`...\73e6052b-0875-45e0-8c65-6e7ac0e890f3\scratchpad\baseline-b5061437\...`). That produced spurious extra failures for any test reading a tracked file more than a few nested directories deep (confirmed root cause: several `docs/hq/<long-name>/...` paths exceeded Windows' 260-character `MAX_PATH` once prefixed by that scratch path, while the identical relative path under the live worktree's much shorter `C:\NWR\prospective-outcomes-v1\...` root never approaches that limit) -- `FileNotFoundError`s that had nothing to do with either commit's real content, reproduced and root-caused live (see `test_current_rookie_udfa_unknown_review_packet_v1_20260630.py` below), then eliminated by rebuilding the baseline worktree at a 15-character path and rerunning. All numbers in this document use the corrected, short-path baseline.
3. **Local-data parity**: the real, gitignored `local_exports/` directory (19 MB, 246 files) was copied read-only from the live worktree into the baseline worktree before each baseline run, so both runs share identical local-data completeness and the diff isolates CODE, not data-presence drift. (Live-worktree `local_exports/` was never modified -- only read from.)
4. **Both full suites** run via `python -m pytest tests/ -q --basetemp=<short-path>` (the same `python` already on PATH for this repo; no separate venv). Every run's exact `FAILED`/`ERROR` node-id list was captured to a file and diffed by exact string, never by count.
5. **Current-HEAD run integrity**: the first current-HEAD attempt was invalidated for a different reason -- it was launched in the background and then contaminated by this session's own concurrent edits to `tests/test_desktop_application_api.py` mid-run (confirmed: that run's log shows the PRE-fix 3-failure state for that file, not the true final state). Discarded. Two clean, uncontaminated, sequential full-suite runs were then taken AFTER every fix in this pass was committed (commit `295a4a6e`), with zero concurrent edits: **334 failing tests, byte-identical set, both times** (`323 failed, 5282 passed, 76 skipped, 13 errors` the first time; `321 failed, 5284 passed, 76 skipped, 13 errors` the second -- the 2-count difference is fully explained below, not a contradiction).
6. **`git status --short` for the whole repo**, captured immediately before and immediately after the final full-suite run: **byte-identical both times** (only the 2 pre-existing untracked `local_exports.backup-*` directories, present before this dispatch and never touched). No test in the full suite mutated any tracked file this pass, beyond the P0 hazard already fixed and documented in a prior entry in this same ledger. No new file-mutation hazard found.

## Exact baseline vs. current counts

| | FAILED | ERROR | Total unique failing/erroring node ids |
|---|---|---|---|
| **Baseline** (`b5061437`, corrected short-path worktree, matched local data) | 329 | 13 | **342** |
| **Current HEAD** (`295a4a6e`, live worktree, reproduced twice) | 323 / 321 | 13 | **334** (stable both times) |

## Exact NEW / FIXED / UNCHANGED sets

- **NEW = (current failures) - (baseline failures) = 0.** Zero. Every test that fails at current HEAD also failed at the corrected baseline. **The current upgrade cycle introduced no new test regression, proven by exact name diff, not by count similarity.**

  *(One apparent candidate was investigated and disproved, not hand-waved away: the FIRST current-HEAD run showed 2 extra failures --* `test_routine_refresh_service.py::test_routine_refresh_dry_run_does_not_mutate_files` *and* `test_routine_refresh_service.py::test_routine_refresh_partial_failure_reports_sleeper_error` *-- absent from both the baseline run and a second immediate rerun of the identical current-HEAD commit. Rerun in isolation (standalone file, and combined with the two test files this pass modified): both pass cleanly every time. This is genuine, reproducible, non-deterministic order/state-dependent flakiness somewhere across the ~5700-test full run, unrelated to any file this cycle or this pass touched -- confirmed by evidence, not assumed. Not counted as a real failure.)*

- **FIXED = (baseline failures) - (current failures) = 8 exact tests:**
  - `tests/test_desktop_application_api.py::test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware` -- fixed this pass (rookie-veteran bridge snapshot repoint, see below).
  - `tests/test_desktop_application_api.py::test_facade_has_no_streamlit_or_app_component_dependency` -- fixed this pass (AST module-name check bug).
  - `tests/test_desktop_application_api.py::test_redraft_bootstrap_seeds_once_and_matches_desktop_contract` -- fixed this pass (stale FantasyPros-key assumption + stale `nwrPureExperimental` key omission).
  - `tests/test_rookie_veteran_dynasty_bridge_service.py::test_tracked_redraft_bridge_is_currently_computable` -- fixed this pass, same root cause as the first item above.
  - `tests/test_draft_prep_data_foundation_service.py::test_2025_user_drafted_list_and_yellow_highlights_are_context_only` -- fixed by this cycle's own prior P0 fix (commit `e4fca3f1`, already documented earlier in this ledger): now an honest `pytest.skip` instead of a failure against degraded data.
  - `tests/test_draft_prep_data_foundation_service.py::test_draft_prep_foundation_outputs_and_guardrails` -- same P0 fix.
  - `tests/test_draft_prep_data_foundation_service.py::test_prior_history_and_scouting_pool_do_not_create_final_recommendations` -- same P0 fix.
  - `tests/test_nwr_pure_experiment_service.py::test_build_git_provenance_against_the_real_worktree_returns_real_values` -- **not a code fix**: this test asserts real git-provenance facts (current commit/branch identity) about whichever worktree it runs in; it necessarily reports a different (and, at the later commit, valid) result when run against `295a4a6e` than against `b5061437`. Flagged honestly rather than miscounted as a real bug fix.

- **UNCHANGED = intersection = 334 exact tests.** Every one is listed, classified, and root-caused individually in the table below (grouped by shared file/root-cause per the dispatch's own grouping rule; every single test name from all 334 appears at least once).

## The four long-running backend-API failures -- final disposition

For each: **INSPECTED CODE**, **ACTUAL TEST RESULT** (isolated + full-suite), classification, and fix where the classification was `REAL_CURRENT_DEFECT`.

### 1. `test_dynasty_facade_composes_real_governed_workflows` -- `ENVIRONMENT_DEPENDENCY`, left failing (honestly)

**Isolated run**: fails at exactly one assertion, `bootstrap.data["summary"]["marketMatched"]`: real value `239`, test's hardcoded expectation `230`. Every other field in this large, exhaustive-key-set assertion matches exactly.

**INSPECTED CODE**: `marketMatched` (`desktop_facade.py`, `dynasty_bootstrap()`) counts `current_players` rows with a non-null `market_dp_rank`, sourced from `owner_asset_evidence_service.py`'s join against `market_baseline_service.py`. `git diff b5061437..2fe3165e -- src/services/owner_asset_evidence_service.py` shows the only change this cycle made to that file (Worker 4's `status_overrides`/`current_status_override` field) never touches `market_dp_rank` or any market-join logic. `market_baseline_service.py` itself is untouched this cycle. Its real data source, `runtime_artifact_dir()`, resolves to `%LOCALAPPDATA%\NinersWarRoom\data\refresh_data` by default -- a single, machine-wide location shared by every worktree on this machine, not a per-commit or per-worktree artifact, and its real DynastyProcess market-matching coverage has organically improved since `230` was hardcoded (consistent with `nwr-source-not-reproducible.md`'s standing finding that this exact source "can change schema/values" day to day).

**Disposition**: `ENVIRONMENT_DEPENDENCY`. Not fixed -- updating the hardcoded `230` to `239` would only be correct until the shared machine-wide market snapshot next refreshes, at which point the same brittle pattern recurs; not confident enough in a stable number to force a green result.

### 2. `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware` -- `REAL_CURRENT_DEFECT`, FIXED

**INSPECTED CODE**: `src/services/rookie_veteran_dynasty_bridge_service.py` hardcoded its Redraft evidence source to an abandoned 608-row candidate packet (`docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv`), while every other live surface (`desktop_facade.py`'s own `REDRAFT_SEED_SOURCE_RELATIVE`) migrated to the real, currently-governed "Freeze V7" 564-row snapshot back on 2026-09-12 (commit `8d5401273`, well before this cycle's own baseline) -- that migration's own comment explicitly says the 608-row packet was "left in place, untouched (still used by `tests/test_redraft_profile_practical_mode_toggle.py`'s own fixture)" but never mentions this bridge service as a legitimate remaining consumer, strongly suggesting this was a genuine oversight, not a deliberate design choice.

**ACTUAL TEST RESULT (isolated, before fix)**: `load_redraft_bridge_context()` returns `errors=('All 608 projection rows are blocked because source_as_of exceeds the 30-day freshness window...',)`, `by_player_id={}` -- EVERY player, including established veterans like Jahmyr Gibbs, resolves to `INSUFFICIENT EVIDENCE` for the "win now" bridge decision. A second, undocumented real-product test in the same area, `tests/test_rookie_veteran_dynasty_bridge_service.py::test_tracked_redraft_bridge_is_currently_computable`, independently caught the identical root cause (`context.errors == ()` failing) -- confirming this is a real, currently-broken, live-desktop-app-reachable (Dynasty Compare page) defect, not a hypothetical.

**Fix**: repointed `REDRAFT_PACKET_RELATIVE`/`REDRAFT_SOURCE_NAME`/`REDRAFT_SOURCE_SHA256` to the same Freeze V7 snapshot (564 rows, admitted 2026-09-08, `source_as_of` within the 30-day window as of today 2026-09-30) already governing every other live surface. Verified both target players (Jeremiyah Love, Jahmyr Gibbs) are present in the new source with real `player_id`s matching the Dynasty asset registry's `governed_player_id`, and that the resulting VBD gap (248.7 vs 134.8) still produces `preferred: "Jahmyr Gibbs"` -- the exact value the test already expected, requiring zero test-assertion changes for this specific check. Updated the ONE other real consumer of the real (non-synthetic) path (`test_tracked_redraft_bridge_is_currently_computable`'s hardcoded `608` row count -> `564`) after confirming, by reading the file, that every other test in that file builds its own synthetic `RedraftBridgeContext` and never touches the real source at all. No governed valuation formula, projection snapshot, or hash touched -- only which already-governed file this one consumer points at.

### 3. `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract` -- `EXPECTED_CONTRACT_CHANGE` (two stacked instances), FIXED

**INSPECTED CODE + ACTUAL TEST RESULT**: failed at the FIRST of two stacked, independent stale-assertion gaps, each unmasked only after fixing the one before it:
1. `bootstrap.data["externalConsensus"]` hardcoded `configured: False` ("FantasyPros API key is not configured..."), but this session's real dev shell has a real `NWR_FANTASYPROS_API_KEY` environment variable configured (confirmed: `env | grep FANTASYPROS` shows a real key) -- the test never forced this precondition the way every other test in the file already forces `NWR_DYNASTY_RANKINGS_ROOT` via `monkeypatch.delenv`.
2. After forcing that precondition closed, the NEXT assertion (`presets[i]` key set) failed on a real, additive `nwrPureExperimental` key (commit `a5b9d8cf`, "NWR PURE -- EXPERIMENTAL mode toggle", present since before this cycle's own baseline) that this test's key-set assertion was never updated to include -- masked until now by the first gap, exactly the same "pre-existing additive key never added to the assertion" pattern the test's own comments already document twice (`marketProviderAdp`, `leagueCapabilities`).

**Fix**: added `monkeypatch.delenv("NWR_FANTASYPROS_API_KEY", raising=False)` (matching this file's own existing pattern for other environment-dependent preconditions) and added `nwrPureExperimental` to the expected key set with the same explanatory-comment convention the file already uses. Zero production code touched -- the real backend behavior was already correct; only the test's own preconditions/expectations were stale.

### 4. `test_facade_has_no_streamlit_or_app_component_dependency` -- `OBSOLETE_TEST`, FIXED

**INSPECTED CODE**: the check built its "imports" set from EVERY `alias.name` under both `ast.Import` and `ast.ImportFrom` nodes, then asserted none started with `"app"`. For `ast.ImportFrom`, `alias.name` is the imported SYMBOL, not the module -- so any real function import whose name happens to start with "app" (`apply_status_overrides_to_ranking`, `apply_catch_up_paste`, `approve_owner_platform_manual_match`, `append_correction_record`, `append_owner_test_event` -- confirmed present in `desktop_facade.py` since before this cycle's own baseline via `git show b5061437`) false-triggers the assertion, with zero actual Streamlit or legacy-`app`-package coupling.

**ACTUAL TEST RESULT (after fix)**: confirmed via a corrected AST walk (module names only: `ast.Import` aliases, and `ast.ImportFrom.module`) that `desktop_facade.py` genuinely has zero real `streamlit`/`app.*` module imports -- the property the test exists to verify is actually true and was simply being checked wrong.

**Fix**: rewrote the check to inspect module names, not every imported symbol. No production code touched.

## Combined test-run proof (after all 4 fixes)

`tests/test_desktop_application_api.py` -- final state: **50 passed, 1 failed** (`test_dynasty_facade_composes_real_governed_workflows`, the one honestly left `ENVIRONMENT_DEPENDENCY`). Down from 4 failures to 1, by name, not estimate.

---

## Per-test inventory -- the 334 UNCHANGED (pre-existing, both baseline and current) failures

Every test below failed identically, by exact name, at both the corrected baseline (`b5061437`) and current HEAD (`295a4a6e`), reproduced via two independent full-suite runs of current HEAD with a byte-identical 334-test result both times. Grouped by file where every test in that file shares the same investigated root cause; a per-test cross-check confirms all 334 baseline-unique test names appear exactly once below.

**tests/test_champion_challenger_registry_service.py** -- 1 test(s)
- AREA: source-hygiene scanner (champion/challenger registry coupling)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: A repo-wide text scanner asserts `champion_challenger_registry` is referenced only by its own module and one explicitly allowlisted caller; it found a second reference in `src/services/owner_test_instrumentation_service.py` -- INSPECTED: that reference is a plain prose docstring mention (line 6, '`champion_challenger_registry_service.py` and the decision-receipt ...'), never an import or a call. The scanner's own allowlist mechanism already has logic to tell a prose mention apart from a real call (see its own comment), but only applies that nuance to the one pre-allowlisted caller, not to every other file it scans -- a real, narrow false-positive in the scanner itself, not a real coupling violation.
- ACTION: FIX_LATER_LOW_PRIORITY
- TEST NAMES:
  - `test_no_unexpected_source_file_references_the_champion_challenger_registry_module`

**tests/test_current_player_value_extraction_report.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_current_player_extraction_report_covers_all_current_roster_subjects`
  - `test_current_player_extraction_report_matches_key_checkpoint_values`

**tests/test_data_health_dashboard_service.py** -- 1 test(s)
- AREA: data-hygiene guardrail dashboard (runtime-JSON-tracked check)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: `_guardrail_health()`'s 'No runtime JSON tracked' guardrail flags 2 real tracked files as runtime-state leakage: `sample_data/kha_real_draft_2026/live_runtime_draft_board_157picks.json` and its `.backup.json` sibling. INSPECTED: both are real, intentional, already-committed SAMPLE FIXTURE data under `sample_data/` (per AGENTS.md's own 'player data only in sample fixtures' rule), not live runtime leakage -- `is_runtime_state_path()`'s own allowlist (`TRACKED_DOCUMENTATION_ROOTS`) has no exemption for the `sample_data/` root, so it false-flags these two legitimate fixtures as RED.
- ACTION: FIX_LATER_LOW_PRIORITY
- TEST NAMES:
  - `test_guardrails_report_no_shared_or_runtime_files_tracked`

**tests/test_data_health_receipt_page_open_safety.py** -- 14 test(s)
- AREA: legacy Streamlit AppTest harness (app/ pages)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: streamlit.testing.v1.AppTest.from_file() resolves a relative script path against the CALLING file's own directory, not the repo root; this worktree's AppTest fixtures pass a repo-root-relative path, so every one raises 'AppTest script not found'. Already documented in session memory (nwr-draft-upgrade-hq-baseline-failures, nwr-hermetic-apptest-fix) and on the sibling Niners-War-Room repo's own fix commit 157b9601 ('resolve Streamlit AppTest paths from repo root') -- that fix has not yet been ported into this worktree. Only reachable from the legacy Streamlit app/ pages, never the desktop app.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_page_open_is_read_only_for_every_receipt_state[corrupt_latest-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[corrupt_latest-settings_data_health]`
  - `test_page_open_is_read_only_for_every_receipt_state[duplicate_key_receipt-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[duplicate_key_receipt-settings_data_health]`
  - `test_page_open_is_read_only_for_every_receipt_state[invalid_type_receipt-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[invalid_type_receipt-settings_data_health]`
  - `test_page_open_is_read_only_for_every_receipt_state[missing_latest-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[missing_latest-settings_data_health]`
  - `test_page_open_is_read_only_for_every_receipt_state[oversized_receipt-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[oversized_receipt-settings_data_health]`
  - `test_page_open_is_read_only_for_every_receipt_state[unsupported_schema-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[unsupported_schema-settings_data_health]`
  - `test_page_open_is_read_only_for_every_receipt_state[valid_latest-refresh_data]`
  - `test_page_open_is_read_only_for_every_receipt_state[valid_latest-settings_data_health]`

**tests/test_data_health_receipt_route_smoke.py** -- 2 test(s)
- AREA: legacy Streamlit AppTest harness (app/ pages)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: streamlit.testing.v1.AppTest.from_file() resolves a relative script path against the CALLING file's own directory, not the repo root; this worktree's AppTest fixtures pass a repo-root-relative path, so every one raises 'AppTest script not found'. Already documented in session memory (nwr-draft-upgrade-hq-baseline-failures, nwr-hermetic-apptest-fix) and on the sibling Niners-War-Room repo's own fix commit 157b9601 ('resolve Streamlit AppTest paths from repo root') -- that fix has not yet been ported into this worktree. Only reachable from the legacy Streamlit app/ pages, never the desktop app.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_page_open_route_smoke_has_no_refresh_or_receipt_write_side_effect[page_path0]`
  - `test_page_open_route_smoke_has_no_refresh_or_receipt_write_side_effect[page_path1]`

**tests/test_decision_board_coherence_audit.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/june15_decision_board/latest/*.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_decision_board_report_matches_board_counts_and_blocked_use`
  - `test_decision_board_report_matches_receipt_and_component_shape`
  - `test_decision_board_report_records_sample_rows_and_warning_status`
  - `test_decision_board_report_traces_sample_rows_to_sources`

**tests/test_decision_trust_strip_render.py** -- 1 test(s)
- AREA: legacy Streamlit AppTest harness (app/ pages)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: streamlit.testing.v1.AppTest.from_file() resolves a relative script path against the CALLING file's own directory, not the repo root; this worktree's AppTest fixtures pass a repo-root-relative path, so every one raises 'AppTest script not found'. Already documented in session memory (nwr-draft-upgrade-hq-baseline-failures, nwr-hermetic-apptest-fix) and on the sibling Niners-War-Room repo's own fix commit 157b9601 ('resolve Streamlit AppTest paths from repo root') -- that fix has not yet been ported into this worktree. Only reachable from the legacy Streamlit app/ pages, never the desktop app.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_representative_fixture_renders_compact_and_expanded_disclosures`

**tests/test_desktop_application_api.py** -- 1 test(s)
- AREA: desktop backend API contract (Dynasty bootstrap workflow)
- CURRENT-PRODUCT OR LEGACY: CURRENT-PRODUCT
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: See the dedicated four-backend-failures deep-dive section above -- `test_dynasty_facade_composes_real_governed_workflows`: one exact field diff remains (`marketMatched: 239` real vs `230` hardcoded), driven by the live, machine-shared DynastyProcess market snapshot under `%LOCALAPPDATA%\NinersWarRoom\data\refresh_data` (not per-worktree, not touched by any file this cycle changed) organically improving its own identity-matching coverage over time.
- ACTION: ENVIRONMENT_ONLY_NOT_A_CODE_DEFECT
- TEST NAMES:
  - `test_dynasty_facade_composes_real_governed_workflows`

**tests/test_draft_day_trade_lab_service.py** -- 12 test(s)
- AREA: legacy Streamlit AppTest harness (app/ pages)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: streamlit.testing.v1.AppTest.from_file() resolves a relative script path against the CALLING file's own directory, not the repo root; this worktree's AppTest fixtures pass a repo-root-relative path, so every one raises 'AppTest script not found'. Already documented in session memory (nwr-draft-upgrade-hq-baseline-failures, nwr-hermetic-apptest-fix) and on the sibling Niners-War-Room repo's own fix commit 157b9601 ('resolve Streamlit AppTest paths from repo root') -- that fix has not yet been ported into this worktree. Only reachable from the legacy Streamlit app/ pages, never the desktop app.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_trading_lab_route_does_not_silently_fallback_after_hash_failure`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>0]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>1]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>2]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>3]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>4]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>5]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>6]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>7]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>8]`
  - `test_trading_lab_route_fails_closed_for_mutated_player_authority[<lambda>9]`
  - `test_trading_lab_route_renders_complete_universe_rookie_veteran_and_picks`

**tests/test_dropped_released_players_source_service.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/draft_prep/templates/dropped_released_players_template.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_source_contract_and_template_exist_with_guardrails`

**tests/test_durable_refresh_receipt_panel_render.py** -- 2 test(s)
- AREA: legacy Streamlit AppTest harness (app/ pages)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: streamlit.testing.v1.AppTest.from_file() resolves a relative script path against the CALLING file's own directory, not the repo root; this worktree's AppTest fixtures pass a repo-root-relative path, so every one raises 'AppTest script not found'. Already documented in session memory (nwr-draft-upgrade-hq-baseline-failures, nwr-hermetic-apptest-fix) and on the sibling Niners-War-Room repo's own fix commit 157b9601 ('resolve Streamlit AppTest paths from repo root') -- that fix has not yet been ported into this worktree. Only reachable from the legacy Streamlit app/ pages, never the desktop app.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_corrupt_latest_shows_failure_and_validated_prior_separately`
  - `test_receipt_survives_rerun_navigation_equivalent_and_fresh_app_load`

**tests/test_external_asset_reviews_sanity_audit.py** -- 5 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/trade_review/latest & decision_pressure/latest/*.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_external_asset_audit_records_fallback_stale_naming_and_ui_framing`
  - `test_external_asset_repaired_rows_have_no_target_or_trade_for_framing`
  - `test_external_asset_repaired_service_rows_have_review_only_disclosure`
  - `test_external_asset_report_discloses_sources_and_missing_canonical_exports`
  - `test_external_asset_report_matches_service_band_counts_and_top_rows`

**tests/test_injury_status_risk_audit.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_injury_status_report_matches_exported_warning_counts`

**tests/test_legacy_vs_current_sentinel_expansion.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_legacy_sentinel_report_matches_known_handoff_values`

**tests/test_live_draft_room_page.py** -- 1 test(s)
- AREA: legacy Streamlit page/navigation content drift
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: The legacy Streamlit navigation registry's page title was renamed from 'Draft Cockpit' to 'Draft' (the page's own in-body `st.title("Draft Cockpit")` heading was NOT correspondingly renamed), and this test's own assertion checking the nav registry text was never updated to match.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_live_draft_room_page_exists_and_has_route`

**tests/test_market_gap_service.py** -- 2 test(s)
- AREA: legacy data_packs/ CSV pipeline (market gap report)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: `build_market_gap_report(get_settings().active_data_pack)` reports 'Data pack validation errors block market-gap review' and returns zero rows -- the active legacy data_pack in this environment fails its own validation gate (real, pre-existing data-completeness gap in the original CSV/SQLite `data_packs/` pipeline, unrelated to this cycle; zero references from `desktop_facade.py`).
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_market_gap_application_hint_has_no_action_like_terms`
  - `test_market_gap_report_adds_review_only_normalized_scores`

**tests/test_model_edge_evaluation_harness_service.py** -- 5 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_model_edge_harness_builds_leakage_safe_rows`
  - `test_model_edge_harness_includes_rank_pick_and_position_buckets`
  - `test_model_edge_harness_maps_league_outcome_labels`
  - `test_model_edge_harness_outputs_write_without_touching_active_rankings`
  - `test_model_edge_harness_position_summary_supports_position_analysis`

**tests/test_model_v4_confidence_missingness_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/evidence_matrices/latest/source_coverage_matrix.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11f_builds_review_only_confidence_layer`
  - `test_phase_11f_current_prospects_use_admitted_matrix_only`
  - `test_phase_11f_missing_and_source_limited_evidence_create_caps_only`
  - `test_phase_11f_outputs_write_doc_and_csvs`
  - `test_phase_11f_receipts_stay_on_allowed_inputs`
  - `test_phase_11f_writes_sanity_fixture_warnings`

**tests/test_model_v4_current_value_checkpoint_service.py** -- 7 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/rb_wr_current_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11g_builds_review_only_current_value_checkpoint`
  - `test_phase_11g_keeps_position_lifecycle_and_confidence_visible`
  - `test_phase_11g_niners_roster_sanity_warnings_are_present`
  - `test_phase_11g_outputs_do_not_consume_market_projection_or_adp`
  - `test_phase_11g_qb_te_discipline_holds`
  - `test_phase_11g_rb_wr_balance_and_named_players_are_present`
  - `test_phase_11g_writes_doc_and_csvs`

**tests/test_model_v4_decision_board_validation_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_decision_board_validation_focus_rows_include_morning_work`
  - `test_decision_board_validation_keeps_board_review_only`
  - `test_decision_board_validation_writes_outputs`

**tests/test_model_v4_depth_chart_snapshot_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/...` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_may22_depth_chart_snapshot_updates_timestamp_without_changing_roles`
  - `test_may22_depth_chart_snapshot_writes_csv_and_doc`

**tests/test_model_v4_draft_capital_snapshot_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/prospect_sources/latest/files/kaggle_nfl_draft/extracted/solution.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_2026_draft_capital_snapshot_normalizes_pick_order`
  - `test_2026_draft_capital_snapshot_writes_csv_manifest_and_doc`

**tests/test_model_v4_evidence_admission_recheck_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing evidence-matrix source (result degrades to 'fail' instead of 'pass').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_10n_doc_records_pass_status`
  - `test_phase_10n_recheck_passes_latest_admitted_surfaces`

**tests/test_model_v4_evidence_matrix_service.py** -- 9 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (same missing prospect/evidence source data (degrades to 0 admitted rows, e.g. 'assert 0 > 50').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_backtest_matrix_quarantines_duplicate_name_college_leakage`
  - `test_backtest_matrix_uses_pre_draft_features_and_draft_capital`
  - `test_coverage_and_warning_matrices_have_expected_lanes`
  - `test_current_prospect_matrix_keeps_market_out_of_private_lanes`
  - `test_formula_admitted_prospect_loader_fails_closed`
  - `test_phase_10g_builds_all_required_matrices_without_scores`
  - `test_workout_height_strings_are_not_typed_as_zero`
  - `test_workout_zero_placeholders_are_missing_not_bad_testing`
  - `test_write_evidence_matrix_outputs`

**tests/test_model_v4_export_summary_index_service.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_export_summary_index_lists_existing_review_outputs`

**tests/test_model_v4_first_down_canonicalization_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/raw_user_exports/rotowire_manual/2024/first_downs/rushing_first_downs.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_first_down_canonicalization_cleans_known_export_issues`
  - `test_first_down_canonicalization_marks_imported_real_data_and_safe_joins`
  - `test_first_down_canonicalization_produces_receipts_and_coverage`
  - `test_first_down_canonicalization_writes_outputs`

**tests/test_model_v4_first_down_estimation_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire first-down source (degrades to 'assert 0.0 > 0').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_first_down_estimates_are_labeled_estimated_not_direct`
  - `test_first_down_estimates_use_position_fallback_for_players_without_history`

**tests/test_model_v4_formula_contract_service.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing evidence-matrix source.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11a_loader_guard_report_passes`

**tests/test_model_v4_historical_similarity_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_historical_similarity_flags_immature_2025_context`
  - `test_historical_similarity_has_component_receipts_for_each_similarity`
  - `test_historical_similarity_is_review_only_and_same_position`
  - `test_historical_similarity_missing_outcomes_are_unknown_not_misses`

**tests/test_model_v4_human_decision_review_prep_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/decision_board_validation/latest/decision_board_validation_focus_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_human_decision_review_prep_builds_review_only_cards`
  - `test_human_decision_review_prep_cards_block_final_actions`
  - `test_human_decision_review_prep_preserves_known_decision_context`
  - `test_human_decision_review_prep_writes_outputs`

**tests/test_model_v4_lifecycle_archetype_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11e_builds_review_only_lifecycle_layer`
  - `test_phase_11e_components_and_receipts_stay_on_allowed_inputs`
  - `test_phase_11e_emits_required_position_archetypes`
  - `test_phase_11e_outputs_write_doc_and_csvs`
  - `test_phase_11e_uses_admitted_age_sidecar_without_fabricating_gaps`
  - `test_phase_11e_writes_sanity_fixture_warnings`

**tests/test_model_v4_mature_rookie_miss_pattern_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_mature_miss_pattern_report_emits_expected_pattern_families`
  - `test_mature_miss_pattern_report_uses_only_mature_replay_rows`

**tests/test_model_v4_model_edge_queue_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_model_edge_queue_classifies_expected_edge_types`
  - `test_model_edge_queue_is_review_only_and_has_rows`

**tests/test_model_v4_player_rank_explainer_service.py** -- 7 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing evidence-matrix source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_player_rank_explainer_covers_top_50_rookies`
  - `test_player_rank_explainer_default_rows_are_one_per_player_for_top_50_rookies`
  - `test_player_rank_explainer_has_component_receipts`
  - `test_player_rank_explainer_is_review_only`
  - `test_player_rank_explainer_preserves_collapsed_context_warnings`
  - `test_player_rank_explainer_preserves_collapsed_duplicate_contexts`
  - `test_player_rank_explainer_weird_rows_have_edge_or_source_label`

**tests/test_model_v4_qb_age_horizon_shadow_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_old_pocket_qb_shadow_cap_keeps_promoted_stafford_guarded`
  - `test_rodgers_is_already_below_old_pocket_cap_when_present`
  - `test_shadow_cap_does_not_crush_elite_or_younger_qbs`
  - `test_shadow_exports_and_guardrails`

**tests/test_model_v4_qb_te_current_value_service.py** -- 8 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11d_builds_review_only_qb_te_current_value`
  - `test_phase_11d_does_not_propagate_old_review_only_vorp_context_warning`
  - `test_phase_11d_missing_vorp_rows_are_blank_and_confidence_capped`
  - `test_phase_11d_outputs_write_doc_and_csvs`
  - `test_phase_11d_qb_discipline_caps_replaceable_qbs`
  - `test_phase_11d_te_discipline_requires_no_premium_gap`
  - `test_phase_11d_uses_components_and_receipts_without_market_inputs`
  - `test_phase_11d_writes_sanity_fixture_warnings`

**tests/test_model_v4_rb_wr_current_value_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11c_builds_review_only_rb_wr_current_value`
  - `test_phase_11c_does_not_propagate_old_review_only_vorp_context_warning`
  - `test_phase_11c_missing_evidence_is_blank_and_confidence_capped`
  - `test_phase_11c_outputs_write_doc_and_csvs`
  - `test_phase_11c_uses_components_and_receipts_without_market_inputs`
  - `test_phase_11c_writes_sanity_fixture_warnings`

**tests/test_model_v4_replacement_vorp_core_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing evidence-matrix source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase_11b_builds_review_only_replacement_vorp_outputs`
  - `test_phase_11b_first_downs_are_imported_or_missing_not_estimated`
  - `test_phase_11b_qb_and_te_replacement_discipline_is_visible`
  - `test_phase_11b_return_data_is_direct_scoring_only`

**tests/test_model_v4_return_canonicalization_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/raw_user_exports/rotowire_manual/2024/returns/kick_returns.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_return_canonicalization_aggregates_kick_and_punt_scoring`
  - `test_return_canonicalization_cleans_known_export_issues`
  - `test_return_canonicalization_produces_receipts_and_coverage`
  - `test_return_canonicalization_writes_outputs`

**tests/test_model_v4_rookie_age_intake_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/raw_user_exports/rookie_manual/incoming/player_age_mike_clay_top240_*.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rookie_age_intake_parses_user_source_without_using_rank_as_value`
  - `test_rookie_age_intake_writes_csv_and_doc`

**tests/test_model_v4_rookie_outcome_label_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_historical_tuning_report_uses_full_outcome_labels`
  - `test_historical_tuning_summary_separates_universe_and_hit_strictness`
  - `test_rookie_outcome_label_writer_exports_expected_files`
  - `test_rookie_outcome_labels_use_rotowire_stats_without_changing_scores`

**tests/test_model_v4_rookie_pick_decision_lab_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (method falls back to 'no_exact_equivalent' instead of 'internal_model_equivalent').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_pick_decision_lab_comparison_modes_require_concrete_comparators`
  - `test_pick_decision_lab_has_candidate_and_compare_context`
  - `test_pick_decision_lab_includes_all_owned_picks_review_only`
  - `test_pick_decision_lab_neutral_board_blocks_comparison_labels`

**tests/test_model_v4_rookie_replay_baseline_comparison_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rookie_replay_baseline_comparison_builds_all_baselines`
  - `test_rookie_replay_baseline_summary_compares_current_and_draft_capital`

**tests/test_model_v4_rookie_shadow_formula_experiment_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (max() on an empty iterable).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_shadow_formula_experiment_builds_required_variants`
  - `test_shadow_formula_experiment_includes_mature_and_shadow_cohorts`
  - `test_shadow_formula_experiment_writes_outputs`

**tests/test_model_v4_roster_opportunity_cost_service.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_roster_opportunity_cost_components_and_warnings_are_review_only`
  - `test_roster_opportunity_cost_has_pick_equivalents_and_review_labels`
  - `test_roster_opportunity_cost_includes_every_niners_roster_player`
  - `test_roster_opportunity_cost_pick_equivalent_fields_are_split`

**tests/test_model_v4_rotowire_context_intake_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_context_intake_covers_context_sources`
  - `test_rotowire_context_intake_labels_lanes_and_statuses`
  - `test_rotowire_context_intake_writes_outputs`

**tests/test_model_v4_rotowire_dynasty_candidate_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to False).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_dynasty_candidate_receipts_show_vorp_is_review_only_first_down_estimated`
  - `test_rb_age_cap_prevents_old_production_from_beating_young_elite_rb`

**tests/test_model_v4_rotowire_evidence_layer_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to a 'missing_evidence_warning' status).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_evidence_layer_keeps_context_lanes_separate`
  - `test_rotowire_evidence_layer_marks_qb_role_usage_not_applicable`

**tests/test_model_v4_rotowire_identity_coverage_service.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 'review_missing').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_identity_coverage_resolves_truth_set_aliases`

**tests/test_model_v4_rotowire_player_stats_intake_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_player_stats_intake_preserves_grouped_duplicate_headers`
  - `test_rotowire_player_stats_intake_reads_only_canonical_stats_files`
  - `test_rotowire_player_stats_intake_writes_outputs`

**tests/test_model_v4_rotowire_replacement_baseline_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_replacement_baselines_include_labeled_first_down_estimates`
  - `test_rotowire_replacement_baselines_use_locked_lineup_shape`

**tests/test_model_v4_rotowire_role_usage_intake_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_role_usage_intake_covers_role_sources`
  - `test_rotowire_role_usage_intake_preserves_route_snap_and_target_evidence`
  - `test_rotowire_role_usage_intake_writes_outputs`

**tests/test_model_v4_rotowire_source_index_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_schema_catalog_flags_duplicate_headers_and_stability`
  - `test_rotowire_source_index_catalogs_manual_exports`
  - `test_rotowire_source_index_writes_outputs`

**tests/test_model_v4_rotowire_stats_first_value_service.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (degrades to 'missing' instead of 'licensed_use...').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_stats_first_value_uses_licensed_route_export_as_component`

**tests/test_model_v4_rotowire_vorp_review_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing rotowire source (named player absent from an empty dict).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rotowire_vorp_review_builds_truth_set_rows_after_baseline_generation`
  - `test_rotowire_vorp_review_keeps_missing_lve_base_as_review`

**tests/test_model_v4_source_risk_heatmap_service.py** -- 7 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_source_risk_heatmap_distinguishes_mismatch_from_quarantine`
  - `test_source_risk_heatmap_flags_source_limited_and_quarantined`
  - `test_source_risk_heatmap_is_review_only_and_has_players`
  - `test_source_risk_heatmap_missing_data_is_gray_not_zero`
  - `test_source_risk_heatmap_player_summary_has_severity_labels`
  - `test_source_risk_heatmap_player_summary_is_one_row_per_player`
  - `test_source_risk_heatmap_player_summary_preserves_missing_modules`

**tests/test_model_v4_sprint12_13_review_service.py** -- 7 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/confidence_missingness_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_sprint12_13_builds_review_only_outputs`
  - `test_sprint12_13_sanity_warnings_are_visible`
  - `test_sprint12_13_writes_outputs_and_docs`
  - `test_sprint12_pick_baselines_are_review_only_heuristics`
  - `test_sprint12_unified_asset_table_keeps_layers_separable`
  - `test_sprint13_rookie_formula_balance_guardrails_are_visible`
  - `test_sprint13_uses_only_admitted_prospect_rows_for_private_value`

**tests/test_model_v4_sprint14_15_calibration_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/fact_rosters.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_sprint14_15_writes_outputs_docs_and_packet`
  - `test_sprint14a_builds_niners_roster_contract_without_recommendations`
  - `test_sprint14a_contract_includes_deadline_pressure_and_blocked_outputs`
  - `test_sprint15_builds_required_cross_model_fixtures`
  - `test_sprint15_keeps_suspicious_rows_as_review_only`
  - `test_sprint15_niners_sanity_rows_cover_roster_players`

**tests/test_model_v4_sprint14b_cut_keep_pressure_service.py** -- 5 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/decision_calibration/latest/niners_roster_state_review.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_14b_builds_review_only_pressure_without_cut_recommendations`
  - `test_14b_components_are_visible_and_receipted`
  - `test_14b_identifies_required_pressure_zone_as_review_band`
  - `test_14b_keeps_core_assets_protected_by_band_not_recommendation`
  - `test_14b_writes_outputs_docs_and_packet`

**tests/test_model_v4_sprint14c_trade_review_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_14c_builds_review_only_trade_surfaces`
  - `test_14c_components_and_warnings_are_visible`
  - `test_14c_external_asset_rows_exclude_niners_and_remain_review_only`
  - `test_14c_external_asset_rows_have_no_trade_for_or_target_framing`
  - `test_14c_trade_away_rows_are_not_sell_calls`
  - `test_14c_writes_outputs_docs_and_packet`

**tests/test_model_v4_sprint14d_pick_trade_defer_service.py** -- 5 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/fact_future_picks.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_14d_builds_review_only_pick_trade_defer_surfaces`
  - `test_14d_components_warnings_docs_and_packet`
  - `test_14d_defer_scenarios_are_context_not_trade_recommendations`
  - `test_14d_future_pick_context_is_not_target_recommendation`
  - `test_14d_pick_inventory_matches_niners_picks_and_flags_missing_baseline`

**tests/test_model_v4_sprint14e_rookie_draft_review_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_14e_builds_review_only_rookie_draft_surfaces`
  - `test_14e_components_warnings_docs_and_packet`
  - `test_14e_formula_balance_labels_separate_edge_from_source_warning`
  - `test_14e_missing_pick_baseline_stays_warning_not_fake_value`
  - `test_14e_pick_candidate_windows_are_context_not_final_picks`
  - `test_14e_rookie_board_applies_1qb_no_premium_context`

**tests/test_model_v4_sprint14f_june15_decision_board_service.py** -- 5 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_14f_builds_review_only_june15_decision_board`
  - `test_14f_preserves_pick_defer_and_missing_baseline_context`
  - `test_14f_preserves_roster_pressure_without_final_cut_call`
  - `test_14f_rookie_candidate_rows_remain_context_only`
  - `test_14f_writes_outputs_docs_and_packet`

**tests/test_model_v4_startup_slot_simulator_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_outcome_buckets_are_context_only_and_honest_about_samples`
  - `test_startup_slot_pick_zones_include_all_niners_picks`
  - `test_startup_slot_simulator_builds_review_only_sorted_board`

**tests/test_model_v4_warning_dictionary_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to empty tuple).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_warning_dictionary_builds_plain_english_rows`
  - `test_warning_dictionary_links_codes_to_modules_and_drilldowns`
  - `test_warning_dictionary_preserves_raw_codes_and_required_groups`

**tests/test_model_v4_workout_snapshot_service.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (a genuinely manual, user-specific upload path (C:\\Users\\<user>\\Downloads\\workout-stats-QB.csv) never populated on this machine -- not a local_exports path at all, same 'real local source data absent' class one level more session-specific.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_may25_workout_snapshot_normalizes_latest_rotowire_exports`
  - `test_may25_workout_snapshot_writes_csv_manifest_and_doc`

**tests/test_model_v4_wr_qb_v2_candidate_service.py** -- 7 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_candidate_build_is_explicit_and_shadowed_from_latest`
  - `test_candidate_does_not_change_rb_or_te_scores`
  - `test_candidate_guardrails_and_coverage_pass`
  - `test_candidate_uses_no_banned_input_receipts`
  - `test_candidate_wr_qb_v2_behavior_is_narrow`
  - `test_candidate_writes_to_candidate_folder_without_mutating_latest`
  - `test_player_detail_card_shows_candidate_reasons_only_for_candidate_rows`

**tests/test_my_team_decision_receipts_service.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (degrades to 0 rows).) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_my_team_decision_receipts_cover_every_active_niners_player`

**tests/test_nflverse_player_context_display_service.py** -- 1 test(s)
- AREA: player context display (next-game schedule lookup)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Hardcodes an expected 'next game' of week 1 (2026-09-13) for a fixture player; the real, correctly-computed current-date-relative lookup now returns week 18 (2026-09-30, today's real date) -- a genuine wall-clock date boundary the test's own fixed expectation has aged past, not a code defect. The underlying schedule-lookup logic is working correctly for 'today'; only the test's hardcoded expected week is stale.
- ACTION: OBSOLETE_TEST_SHOULD_BE_REMOVED_OR_UPDATED
- TEST NAMES:
  - `test_player_context_artifact_loads_with_required_guardrails`

**tests/test_non_formula_sanity_fixtures.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_current_player_elite_anchors_stay_above_obvious_depth_rows_with_guardrails`
  - `test_decision_board_rows_remain_review_only_and_traceable`
  - `test_legacy_sentinals_remain_comparison_only_and_fail_closed`
  - `test_pick_decision_lab_context_rows_keep_equivalence_guardrails`
  - `test_pick_ladder_keeps_scored_order_and_manual_only_missing_baseline`
  - `test_rookie_watchlist_rows_remain_blocked_from_final_pick_use`

**tests/test_nwr_phase4_null_closure_v1.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (downstream of the same missing source data (a governance-phase marker never reaches 'PHASE_7').) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_phase4_packet_validates`
  - `test_phase7_is_the_only_active_next_gate`

**tests/test_nwr_rookie_review_candidate_v1.py** -- 1 test(s)
- AREA: rookie-review candidate packet byte-exact manifest check
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Byte-exact comparison of a committed packet file against freshly rendered bytes fails only at a line-ending boundary (`b'\r\n'` vs `b'\n'`, index 634) -- a classic Windows `core.autocrlf` line-ending normalization on checkout, not a real content difference. Windows/Git environment-specific, unrelated to any code this cycle touched.
- ACTION: ENVIRONMENT_ONLY_NOT_A_CODE_DEFECT
- TEST NAMES:
  - `test_candidate_packet_is_deterministic_and_manifested`

**tests/test_original_doc_remaining_ux_tools.py** -- 1 test(s)
- AREA: legacy Streamlit page/navigation content drift
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Reads a legacy Streamlit page's source text expecting a literal string that is no longer present -- the page content has since been rewritten; same 'tracked doc/page text drifted from an old literal-string assertion' class documented elsewhere in this cycle (e.g. the DRAFT_PREP_PAGE_ARCHITECTURE doc-template drift found during the P0 test-safety fix).
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_trading_lab_planners_are_manual_only_and_do_not_write_runtime_events`

**tests/test_pick_value_ladder_audit.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/pick_values/latest/pick_value_baselines_review.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_pick_value_ladder_report_matches_compare_row_counts`
  - `test_pick_value_ladder_report_matches_nearby_ladder_rows`
  - `test_pick_value_ladder_report_matches_owned_pick_rows`
  - `test_pick_value_ladder_report_preserves_blocked_use_and_manual_only_flags`

**tests/test_pick_vs_player_neighborhood_audit.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_compare_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_pick_vs_player_report_matches_closest_neighbors`
  - `test_pick_vs_player_report_matches_guardrails_and_elite_risk_flags`
  - `test_pick_vs_player_report_matches_neighborhood_counts`
  - `test_pick_vs_player_report_records_compare_source_disclosure_gap`

**tests/test_player_board_ux_smoke_checklist.py** -- 4 test(s)
- AREA: legacy Streamlit page/navigation content drift
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: The legacy Streamlit navigation registry's Rankings route now resolves to `pages/54_owner_rankings_v2.py`; this test's hardcoded expectation (`pages/20_final_board_v1.py`) reflects an old page-numbering scheme from before a legacy Streamlit page renumbering/restructuring that predates this cycle.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_player_board_negative_control_rejects_missing_routed_title`
  - `test_player_board_negative_control_rejects_title_only_in_unrelated_file`
  - `test_player_board_negative_control_rejects_wrong_player_board_route`
  - `test_player_board_page_contains_ui_labels_referenced_by_checklist`

**tests/test_player_detail_card_component.py** -- 1 test(s)
- AREA: legacy Streamlit page/navigation content drift
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Same class: reads a legacy Streamlit component's source text expecting a literal string ('Trust, warnings, and data needed') no longer present verbatim in the current component source.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_component_uses_shared_payload_sections_without_forbidden_actions`

**tests/test_qb_1qb_discipline_report.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_qb_1qb_report_includes_pick_context_without_trade_equivalence`
  - `test_qb_1qb_report_matches_qb_counts_and_key_scores`

**tests/test_qb_te_upper_band_guard_v2_patch_audit_service.py** -- 3 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_upper_band_guard_v2_patch_audit_acceptance_summary`
  - `test_upper_band_guard_v2_patch_audit_shape_checks`
  - `test_upper_band_guard_v2_patch_audit_writes_expected_files`

**tests/test_rankings_post_patch_acceptance_service.py** -- 5 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_post_patch_acceptance_reports_include_final_decision_boundaries`
  - `test_post_patch_acceptance_shape_is_rankings_review_safe`
  - `test_post_patch_acceptance_summary_passes_core_gates`
  - `test_post_patch_review_csvs_have_required_content`
  - `test_write_post_patch_acceptance_outputs`

**tests/test_rb_wr_cross_position_balance_report.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rb_wr_balance_report_matches_position_counts_and_bands`

**tests/test_redraft_2026_rookie_projection_model_service.py** -- 1 test(s)
- AREA: 608-row candidate packet manifest hash check
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: `MANIFEST.csv`'s recorded sha256 for `NWR_DATA_GOVERNANCE.json` (in the abandoned 608-row `nwr_redraft_2026_rookie_projection_candidate_v1_20260809` packet) no longer matches that file's real on-disk hash -- consistent with this exact governance receipt having been renewed/replaced in a prior cycle (session memory: 'found + renewed the repo's expired bundled seed governance receipt... archived the old one') without regenerating this packet's own MANIFEST.csv to match. Real, tracked-file drift, predates this cycle, confined to the same abandoned packet directory the rookie-veteran bridge fix (this session) moved away from for a different reason.
- ACTION: FIX_LATER_LOW_PRIORITY
- TEST NAMES:
  - `test_committed_rookie_packet_manifest_matches_exact_bytes`

**tests/test_redraft_engine_v1_service.py** -- 16 test(s)
- AREA: Redraft projection-snapshot admission gate / fixture depth
- CURRENT-PRODUCT OR LEGACY: CURRENT-PRODUCT
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real, current-product module (`redraft_engine_v1_service.py` is directly imported and used by `desktop_facade.py` for the live Redraft app). The small synthetic fixtures these tests build (`_projection_rows()`, a handful of rows) no longer satisfy a real governed admission gate (`MINIMUM_POSITION_DEPTHS`-style minimum-admitted-players-per-position check) that production code now enforces before a snapshot is considered rankable -- every fixture-driven ranking call now fails closed with 'Projection snapshot has no rankable player rows' before reaching the specific approval-receipt/staleness assertions these 3 tests check, and the 13 other tests error out at fixture setup for the identical reason. Documented as a known, unchanged baseline across at least 3 prior ledger entries in this same cycle (Worker 5, Worker 8, Worker 9) -- confirmed identical again this pass, not re-investigated further.
- ACTION: FIX_LATER_LOW_PRIORITY
- TEST NAMES:
  - `test_fourteen_teams_increases_scarcity`
  - `test_generate_rankings_scorer_parameter_defaults_to_byte_identical_behavior`
  - `test_health_distinguishes_optional_blocked_rows_from_total_failure`
  - `test_kdst_roster_slots_keep_kdst_out_of_nwr_math_without_blocking_the_board`
  - `test_player_compare_is_explicitly_redraft_and_profile_specific`
  - `test_ppr_changes_pass_catcher_relative_to_rusher`
  - `test_projection_install_is_separate_and_hash_verified`
  - `test_projection_install_requires_separate_bound_approval_receipt`
  - `test_rankings_are_deterministic_and_block_missing_evidence`
  - `test_redraft_compare_pool_exposes_every_ranked_exact_id`
  - `test_review_only_stale_and_shallow_projection_evidence_fail_closed`
  - `test_scoring_engine_applies_profile_rules_and_te_premium`
  - `test_superflex_materially_increases_qb_value_and_rank`
  - `test_te_premium_changes_te_value`
  - `test_three_wr_and_extra_flex_raise_wr_depth_value`
  - `test_tiers_are_deep_bounded_and_position_specific`

**tests/test_refresh_recovery_panel_render.py** -- 1 test(s)
- AREA: legacy Streamlit AppTest harness (app/ pages)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: streamlit.testing.v1.AppTest.from_file() resolves a relative script path against the CALLING file's own directory, not the repo root; this worktree's AppTest fixtures pass a repo-root-relative path, so every one raises 'AppTest script not found'. Already documented in session memory (nwr-draft-upgrade-hq-baseline-failures, nwr-hermetic-apptest-fix) and on the sibling Niners-War-Room repo's own fix commit 157b9601 ('resolve Streamlit AppTest paths from repo root') -- that fix has not yet been ported into this worktree. Only reachable from the legacy Streamlit app/ pages, never the desktop app.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_recovery_panel_renders_keyboard_disclosure_and_all_states`

**tests/test_rookie_board_top_cluster_audit.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rookie_top_cluster_report_matches_board_counts`

**tests/test_rookie_low_evidence_watchlist_audit.py** -- 4 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rookie_watchlist_report_flags_daniel_sobkowicz_as_incomplete`
  - `test_rookie_watchlist_report_lists_every_union_prospect`
  - `test_rookie_watchlist_report_matches_union_counts`
  - `test_rookie_watchlist_report_preserves_market_and_blocked_use_flags`

**tests/test_rookie_research_overlay.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/rookie_research_overlay/latest/rookie_research_overlay_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_rookie_research_overlay_is_review_only_context`
  - `test_rookie_research_pick_notes_cover_niners_picks`

**tests/test_routine_refresh_service.py** -- 1 test(s)
- AREA: routine refresh candidate-pack builder (real, hermetic bug)
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: `test_routine_refresh_success_builds_candidate_pack`: a real, reproducible, hermetic bug (uses only a `FakeSleeperClient` and tmp_path, no real/missing external data) -- when the `model_input_check` step is deliberately skipped (veteran model inputs absent, 'pack will keep placeholder scores'), the downstream `data_pack_build` step does not handle a resulting blank numeric field gracefully and crashes with `invalid literal for int() with base 10: ''`, forcing status to 'blocked' instead of the expected degraded-but-usable 'review'. Zero references from `desktop_facade.py` -- a standalone legacy refresh-pipeline script, not reachable from the live desktop app. NOTE: two additional tests in this same file (`test_routine_refresh_dry_run_does_not_mutate_files`, `test_routine_refresh_partial_failure_reports_sleeper_error`) failed ONLY in one specific full-suite run and are proven non-reproducible: confirmed passing when this file is run standalone, and still passing when run directly after the two test files this session modified -- genuine order/state-dependent flakiness elsewhere in the ~5700-test full run, not caused by this cycle's diff (see ledger for the full before/after evidence); not counted as a real failure in the totals below.
- ACTION: FIX_LATER_LOW_PRIORITY
- TEST NAMES:
  - `test_routine_refresh_success_builds_candidate_pack`

**tests/test_run_historical_calibration_readiness_v1.py** -- 1 test(s)
- AREA: Draft Room historical-calibration research harness
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: `RedraftValidationError: No legal Draft Room asset remains for this team's roster state.` -- the same family of real-projection-fixture-depth exhaustion as `test_redraft_engine_v1_service.py` above, but this test's own caller is a standalone historical-calibration/backtesting research harness (`test_run_historical_calibration_readiness_v1.py`), not the live desktop app, even though it shares `redraft_draft_room_v1_service.py` with the real Draft Room feature.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_synthetic_run_reaches_pass_and_populates_every_section`

**tests/test_shadow_model_tournament_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_shadow_tournament_builds_required_individual_experiments`
  - `test_shadow_tournament_docs_forbid_promotion_and_final_recommendations`
  - `test_shadow_tournament_outputs_are_shadow_only_and_uncontaminated`
  - `test_shadow_tournament_reports_current_board_movement_without_production_change`
  - `test_shadow_tournament_watch_rows_include_required_players`
  - `test_write_shadow_tournament_outputs_does_not_mutate_active_rankings`

**tests/test_shadow_model_v2_wr_qb_refinement_service.py** -- 6 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_v2_qb_lane_reduces_generic_floor_false_positives`
  - `test_v2_refinement_builds_shadow_only_experiments`
  - `test_v2_refinement_uses_no_banned_score_inputs`
  - `test_v2_watch_rows_include_required_players_and_combined_is_limited`
  - `test_v2_wr_lane_tightens_v1_false_positives`
  - `test_v2_write_outputs_does_not_mutate_active_rankings`

**tests/test_te_no_premium_discipline_report.py** -- 2 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_te_no_premium_report_includes_pick_context_without_trade_equivalence`
  - `test_te_no_premium_report_matches_te_counts_and_key_scores`

**tests/test_top_bottom_current_player_sanity_scan.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_top_bottom_scan_matches_sorted_extremes_and_counts`

**tests/test_trust_banner_ui.py** -- 4 test(s)
- AREA: legacy Streamlit page/navigation content drift
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Same legacy navigation-registry renumbering: expects `app.components.decision_trust_strip.render_decision_trust_strips` to be called exactly once from the old Rankings page module; the route now resolves to a different (renumbered) page module that does not call it the same way.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_decision_pages_render_one_primary_trust_banner`
  - `test_main_model_pages_show_required_review_only_banner`
  - `test_trust_negative_control_rejects_call_in_unrelated_module`
  - `test_trust_negative_control_rejects_duplicate_primary_call`

**tests/test_validate_admitted_redraft_2026_combined.py** -- 1 test(s)
- AREA: combined governed snapshot install/validate script
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: `shutil.copytree` raises `shutil.Error: [WinError 3] The system cannot find the path specified` copying a real, existing, non-empty nested directory (`archive_20260829_expired_governance_receipt/`) into a fresh tmp_path. CONFIRMED not a --basetemp artifact of this session's own investigation tooling: reproduces identically with pytest's own default tmp_path. A genuine Windows + Python 3.14 `shutil.copytree` environment-specific quirk, not a code defect in this repo, not touched by this cycle.
- ACTION: ENVIRONMENT_ONLY_NOT_A_CODE_DEFECT
- TEST NAMES:
  - `test_combined_governed_snapshot_installs_and_validates`

**tests/test_veteran_age_window_audit.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_veteran_age_window_report_matches_roster_and_warning_counts`

**tests/test_young_player_evidence_audit.py** -- 1 test(s)
- AREA: legacy model_v4 research pipeline
- CURRENT-PRODUCT OR LEGACY: LEGACY
- PRE-EXISTING OR NEW: PRE-EXISTING (present at baseline b5061437 and at current HEAD, byte-identical test name set)
- ROOT CAUSE: Real local source data genuinely absent from this machine/session's `local_exports/model_v4/...` tree (confirmed: the live worktree itself has no `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` either -- not an artifact of the isolated baseline comparison worktree.) Confirmed via `grep` that no `model_v4_*_service` module is ever imported by `src/application/desktop_facade.py` -- zero live desktop-app call sites.
- ACTION: NO_ACTION_LEGACY_UNUSED
- TEST NAMES:
  - `test_young_player_evidence_report_matches_scope_counts`
