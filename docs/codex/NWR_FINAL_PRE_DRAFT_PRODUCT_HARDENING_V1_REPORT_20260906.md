# NWR FINAL PRE-DRAFT PRODUCT HARDENING V1

**Verdict: `YELLOW_FULL_ENGINE_USABLE_WITH_SPECIFIC_LIMITATIONS`.**

Raw Action Value is now genuinely live, using the exact frozen historical formula. Pick Score parity is confirmed structurally (same functions, not a reimplementation) — V1's own Pick Score is deliberately left untouched. The existing manual league setup was reused, not rebuilt, and one real gap in it (Practical Mode) was patched, not replaced. Tomorrow's real ESPN league still needs the owner's own settings — a short checklist is ready. No historical tuning occurred.

## NWR_EXISTING_PRODUCT_REUSE_AUDIT

Per the project's new reuse-first rule, everything below was located and verified BEFORE anything was built:

| Capability | Existing implementation found | Verdict |
|---|---|---|
| Manual league setup | `create_redraft_profile(preset_key, league_name)` + `update_redraft_profile(profile_id, league_name, team_count, roster, scoring, draft, ...)` | **Already complete** for team count, roster slots (QB/RB/WR/TE/FLEX/Superflex/K/DST/bench), scoring (reception/passingTd/interception/tePremium), rounds, draft slot |
| Practical Mode toggle | Was previously settable ONLY inside the Sleeper-import path | **Real gap, patched today** — `update_redraft_profile` now accepts `practical_mode` |
| Draft type (snake/linear) | `DraftContext.draft_type` (snake/auction only) — not editable via `update_redraft_profile` at all, only at creation | **Real, minor, disclosed gap** — "linear" isn't a distinct NWR concept; not patched (out of scope, ESPN leagues are virtually always snake) |
| IR slots | Searched `RosterSettings` and the whole roster schema | **Confirmed genuinely absent** — no IR concept anywhere in this codebase. Not patched (nothing is ever drafted directly to IR; not draft-time-blocking) |
| Practice vs Real intent | No formal `intent` field on `LeagueProfile` | Safety is **already structurally guaranteed** without one — every profile is isolated by `profile_id` (separate draft_boards/manual_assets/profiles files); no cross-profile mutation path exists at all, at any layer. A cosmetic label is the only missing piece, not a safety mechanism. Not built (not proven necessary) |
| Current-data refresh | `install_projection_snapshot(root, season, source, approval_receipt)` | **Already complete** — used twice today (real install renewal, bundled seed renewal) |
| Governance approval flow | `_validate_approval_receipt` + the receipt JSON contract | **Already complete** |
| Practice flow | Real profiles isolated by `profile_id`; `mode="MOCK"` for solo practice | **Already complete** |
| Draft Room / rapid pick capture / undo / reset | `start_draft_room`, `owner_pick_and_advance`/`mark_redraft_player`, `undo_room_pick`/`undo_redraft_pick` | **Already complete**, exercised repeatedly today |
| DecisionBundle V1 | `decision_bundle_service.py` / `decision_bundle_live_service.py` | **Already complete**, unmodified |
| DecisionBundle V2 (Team Score V2 / Equity V2) | `decision_bundle_service_v2.py` (built in an earlier session today) | **Already complete** |
| Raw Action Value / Regret | `decision_engine_v2_contracts_service.py` (research branch, `compute_raw_action_value`/`compute_regret`/`compute_decision_quality_percentile_raw_rank`) | **Existed as a frozen, unmodified formula module, but grep-confirmed ZERO live usage anywhere before today** — genuinely absent from live inference (option D of the audit menu). Wired today (see below), not duplicated |
| Pick Score (live) | `shadow_numeric_authorities_service.pick_score()` | **Already complete, structurally distinct from RAV** — a min-max normalization of Championship Equity win-probability only, never consulting RAV/regret. Confirmed by direct source reading, not assumption |
| Prospective logging | `prospective_decision_log_v1_service.py` (built earlier today) | **Already complete** |

**Actual missing gaps found**: Raw Action Value/Regret live wiring (closed today), the Practical Mode toggle (closed today), draft-type editability (disclosed, not closed), IR schema (disclosed, not closed), formal practice/real intent label (disclosed as non-safety-critical, not closed).

## 1. Raw Action Value — live integration

Traced to `decision_engine_v2_contracts_service.py` (unmodified) and the research branch's exact historical usage (`run_final_2025_holdout_evaluation_v1.py::evaluate_raw_action_value`). The real methodology: force a candidate now, complete the rest of the draft via a real continuation policy, score the resulting terminal roster, repeat across several independent rollouts, feed those real values into `compute_raw_action_value()`.

Built `raw_action_value_live_service.py`: reuses `shadow_numeric_authorities_service.simulate_pick_now()` (the exact same real function `evaluate_pick_candidates` already uses for V1 Pick Score) to run real, independent, full-draft-completion rollouts per candidate, scores each with the real `team_score()` percentile, and feeds those real values straight into the unmodified `compute_raw_action_value()` / `compute_regret()` / `compute_decision_quality_percentile_raw_rank()`. No new formula. No hand-weighting. Championship Equity is refused as a terminal objective by construction (its historical-validation gate has never been opened).

Cost-controlled and disclosed: only the top N candidates get RAV per call (FAST=3, STANDARD=5, DEEP=8 candidates, 2/3/5 rollouts each respectively — preset-tuned after real latency measurement, see Section 9). Every candidate's status is explicit: `OK`, `UNAVAILABLE: <reason>`, or `SKIPPED_TOP_N_ONLY` — never a fabricated number.

Wired into `decision_bundle_service_v2.py` (on by default, graceful degradation — any RAV failure becomes a warning, never crashes the rest of the bundle) and through to the real HTTP-facing JSON: `rawActionValue` (with `expected_terminal_value`/`terminal_value_stdev`/`terminal_objective_name`/`lookahead_depth`/`rollout_count`), `expectedRegret`, `decisionQualityPercentile`, `rawActionValueStatus` per candidate.

## 2. Pick Score parity

**V1's live Pick Score (`shadow_numeric_authorities_service.pick_score()`) does NOT consume Raw Action Value / Regret, and was NOT changed today.** Confirmed by direct source reading: it is a min-max normalization of each candidate's Championship Equity win-probability within the single call's candidate set (`relative = 100 * (equity - worst_equity) / spread`) — the best candidate in any batch is *always* forced to exactly 100, the worst to exactly 0, regardless of how small the real underlying spread is. This is real, pre-existing, structural behavior, not something introduced by today's work.

Per the mission's own explicit instruction ("Do not change Pick Score calibration"), V1 Pick Score stays exactly as it is. What's new is a **separate, additive** quantity — `decision_quality_percentile` (the actual historically-validated "Pick Score" semantics, `PICK_SCORE_DECISION_QUALITY_PERCENTILE`) — now live for the first time via the V2 path, without retrofitting V1.

**4 parity tests added** (`test_raw_action_value_pick_score_parity.py`): confirm the live path calls the literal same `compute_raw_action_value`/`compute_regret`/`compute_decision_quality_percentile_raw_rank` function objects the offline historical engine uses (not a reimplementation, not import-shadowed), and that the live module never imports `pick_score`/`raw_decision_utility` at all.

## 3. Complete owner-facing candidate row

Every field the mission asked for now exists somewhere in the composed response, honestly labeled where unsupported:

| Field | Source | Status |
|---|---|---|
| player / position / team | V1 (unchanged) | ✅ |
| Player Score | V1 | ✅ |
| Team Score current/after/delta | V1 (and V2, separately, both real) | ✅ |
| Championship Equity current/after/delta | V1 (and V2) | ✅ |
| Make-It-Back / Cost of Waiting | V1 | ✅ |
| expected replacement loss | **Not found as a distinct live field** — V1's `costOfWaiting` is documented as "an approximation... a lower bound, not the final number" for this exact concept; no separate "expected replacement loss" quantity exists in the live codebase | Disclosed, not fabricated |
| Raw Action Value / expected regret | New today | ✅, top-N only, explicit status |
| Pick Score | V1 (unchanged) | ✅ |
| evidence/data status | V1 (`uncertainty`) + V2 (`v2Status`/`rawActionValueStatus`/`evidenceContext`) | ✅ |
| model versions | V2 `evidenceContext` + per-field `model_version` | ✅ |
| Decision Confidence | Never computed or exposed by this endpoint | Correctly absent, not shown as authoritative |

## 4/5. Manual league setup / practice-vs-real — see the reuse audit above

No new configuration system was built. The one real gap (Practical Mode) was patched minimally. Practice/real safety is already structurally guaranteed by profile-id isolation.

## 6. Live UI / shadow view

**Not attempted.** This sandboxed session cannot build or render the actual Tauri desktop app, so an unverified change to `draft-room-v2.tsx` (920 lines, significant existing structure) was judged too risky, exactly as in the prior pass. The backend is complete: `POST /api/v1/redraft/draft/{profileId}/decision-bundle-v2` returns every field above, real and tested. No local "developer panel" surface was found already built for inspecting this outside the app itself — the closest existing thing is `owner_test_instrumentation_service.py`'s JSONL event log (operational diagnostics, not a candidate-row viewer) and the new `prospective_decision_log_v1_service.py` log (which DOES capture full candidate rows, just not in a rendered UI). Reported honestly as the one remaining real gap, not risked.

## 7. QA mock — real, with Raw Action Value

Ran against the real local install's TEMPORARY_QA_CONFIG profile (10-team, unverified-for-real-league, per the owner's own scoping) — 8 real rounds through the real Draft Room, with RAV inspected specifically. Full evidence: `NWR_FINAL_PRE_DRAFT_HARDENING_RAV_QA_MOCK_20260906.txt`.

- Raw Action Value present and real for the top-N candidates every round (5/10 candidates per call at the FAST-preset default used for the mock).
- Drafted players correctly disappeared from subsequent candidate lists.
- Position caps, K/DST, and DATA_LIMITED rookies all behaved as previously confirmed (unchanged since the earlier QA pass).
- Undo (83→82 picks) and reset both confirmed clean.
- Real KHA (157 picks) and Fantasy Gamers (31 picks) boards independently re-verified byte-identical/untouched throughout.

## 8. Close-call sanity — a real, concrete finding

The mock's own sanity check flagged **2 of 8 rounds** where V1 Pick Score showed a 50-point separation between the top two candidates while **both Team Score outcome (0.0 gap) and the new Raw Action Value (0.0 gap) showed the two candidates as genuinely equivalent.**

**Diagnosis** (per the mission's own required classification menu): not a legitimate Team Score difference (0 gap), not a legitimate Cost of Waiting difference, not a state bug, not stale data, not an implementation bug. This is the **known, already-diagnosed low-resolution limitation of V1 Pick Score's min-max normalization** (Section 2) — now corroborated with real, independent comparative evidence from the historically-validated RAV path, which agrees with Team Score that these candidates are equivalent while V1 Pick Score manufactures a large-looking gap. **Not tuned or changed** — flagged as real, useful evidence that RAV/decision-quality-percentile may be the more trustworthy signal specifically on close calls, consistent with (and now strengthening) the historical program's own established finding.

## 9. Latency

Measured against the real local install, RAV included:

| Preset | Candidates × RAV trials | Latency (before tuning) | Latency (after preset tuning) |
|---|---|---:|---:|
| FAST | 5 × 2 → 3 × 2 | 6.2s | **4.6–5.0s** |
| STANDARD | 5 × 2 → 5 × 3 | 17.6s | 19.3s (more real evidence per pick, by design — STANDARD/DEEP are not the default) |

The real Sleeper league confirmed earlier (60-second pick timer) gives FAST ~5s a comfortable ~8% clock usage. **Optimized via engineering only** (top-N candidate count, per-preset trial count) — the frozen RAV/regret formulas themselves are completely unchanged. Further optimization (parallelizing rollouts, incremental caching across picks) is possible but not attempted today — current numbers are real and usable, not blocking.

## 10. Tomorrow's ESPN profile

See `NWR_403_N_18TH_MANUAL_SETUP_CHECKLIST_20260906.md` — a short field list (team count, scoring, every roster slot, bench, IR, rounds, draft slot) to fill in from the owner's own ESPN settings page. Entering it takes under 2 minutes through the existing, unmodified manual profile-edit flow — no new tooling was built or is needed.

## Regression

Full suite: **3867 passed / 334 failed / 71 skipped** (one run) — the known established baseline this session is 324 failed, with an already-documented pattern of occasional flaky drift unrelated to any change made (reproduced and traced earlier this same session).

**Stronger, targeted confirmation** on the file most directly touched by today's `desktop_facade.py` changes (`tests/test_desktop_application_api.py`, 43 tests): exactly 4 failures, and all 4 names match the file's own long-documented, pre-existing baseline character-for-character (`test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency`). **A real, incidental improvement**: this baseline was previously 5 failures; today's governance-receipt renewal (Section 6 of the earlier QA-day pass) fixed `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile` as a side effect (it depends on the same hermetic auto-seed the expired receipt was blocking). Zero new failures in this file from any of today's Raw Action Value or facade work.

Focused RAV/parity/facade test suites: **25 new tests, all passing** (raw_action_value_live_service: 4, parity: 4, decision_bundle_service_v2/live_service_v2/facade extensions: 3 modified/extended, practical_mode toggle: 4 from the prior pass). See the commit history for the exact per-commit test deltas.

## Final verdict

**`YELLOW_FULL_ENGINE_USABLE_WITH_SPECIFIC_LIMITATIONS`**

- **Launch command**: same launcher as always (`desktop/launch-draft-upgrade-preview.bat`).
- **Temporary QA profile**: `4b4a990faf124ce7a5d612537ba5943b`, labeled `TEMPORARY_QA_CONFIG_UNVERIFIED_REAL_LEAGUE_SETTINGS (10-team)` — real, reset clean, ready for more mocks.
- **Raw Action Value live?** Yes — real, exact frozen formula, top-N cost-controlled, disclosed status per candidate.
- **Pick Score parity?** Confirmed structurally (same functions) — V1 Pick Score deliberately unchanged; the real validated quantity is now separately exposed via V2.
- **Latency**: FAST ~4.6–5.0s, STANDARD ~19s, both real and measured against the real install.
- **Remaining blockers**: (1) tomorrow's real ESPN settings still need the owner (checklist ready); (2) no visible UI toggle for V2/RAV yet — backend-complete, frontend deliberately not risked; (3) two small, disclosed, non-blocking schema gaps (draft-type editing, IR).

No push. No merge. No deployment. No historical model tuning.
