# NWR DRAFT ROOM CONSOLIDATION V1 — REPORT (+ addendum)

**Verdict: `YELLOW_CONSOLIDATED_DRAFT_ROOM_NEEDS_FOLLOWUP`.**

One critical, real, reproduced bug was found and fixed. One real capability (position-demand-aware Make-It-Back) was confirmed to already exist and work — no duplicate system was built. One real root cause (Puka Nacua's missing alert) was traced to a stale, manually-refreshed local data file. **No frontend/UI consolidation work was attempted** — this sandboxed session cannot build or render the Tauri desktop app, and risking an unverified change to either Draft Room the night before a real draft was judged unacceptable. This is the honest, single biggest gap in this report; it needs a session with real GUI build/render access, or the owner's own hands-on work guided by the spec below.

## 1. CRITICAL BUG — Fantasy Gamers candidate collapse — FOUND, FIXED, VERIFIED

**Reproduced exactly** against the real Fantasy Gamers profile (read-only — never called any state-mutating function against it; only flipped the global active-profile pointer, which touches no per-profile data, and restored it immediately after each read). All 8 real candidates (Stafford, Maye, Etienne, Flowers, Lawrence, Jacobs, Swift, Adams) returned identical Pick Score 50.0 / Team Score 90.0 (+80.0) / Equity 25.0%, exactly as reported.

**Traced layer by layer**:
1. `simulate_pick_now()` (real, unmodified) — confirmed NOT a state-clone bug. Diffing the 4 traced final rosters showed 13-15 of 15 players overlapping, genuinely different, not literally identical.
2. `team_score()`'s `.percentile` — **the collapse point. `TEAM_SCORE_SATURATION`.** Percentile is bucketed against the comparable-league population (population_size = trials × team_count — only 20 at the live FAST preset). Several genuinely-different, similarly-strong real terminal rosters deep in a draft land in the identical bucket.
3. Championship Equity inherits the same saturation (`EQUITY_SATURATION`, same root cause).
4. V1's live `pick_score()` — its equity-win-probability min-max normalization correctly, mechanically falls back to a flat 50.0 for every candidate when its only differentiating input (win_probability) ties exactly. This is real, disclosed, structural behavior of the already-shipped formula — **not modified**, per this session's own standing safety rule to preserve the real-draft fallback path.

**Fix, deliberately narrow**: `raw_action_value_live_service.py` (this session's own new module, not V1's shipped `pick_score()`/`team_score()`) now feeds `team_score()`'s real, continuous, un-bucketed `.roster_value` into `compute_raw_action_value()` instead of `.percentile`. Same real Team Score output, same unmodified `compute_raw_action_value()`/`compute_regret()`/`compute_decision_quality_percentile_raw_rank()` functions — only which real number is extracted from an already-computed result changed, not any formula.

**Verified fixed** against the real scenario: Stafford 989.84 (regret 23.0), Maye 983.44 (regret 29.4, worst), Etienne 1012.84 (regret 0.0, best, decision-quality percentile 100) — real, credible, differentiated evaluation.

**Regression fixture added** (`test_mixed_position_candidates_deep_in_a_draft_do_not_collapse_to_identical_values`): reproduces the exact structural conditions synthetically; confirmed it FAILS against the pre-fix code (reproduces the bug: 5/5 candidates collapse to 100.0) and PASSES with the fix.

## 2. RAV / counterfactual pick-evaluation audit

Audited (not duplicated) the existing `evaluate_pick_candidates`/`raw_action_value_live_service` pipeline. With the fix above, RAV now genuinely differentiates real candidates by real projected outcome, which is the prerequisite for the "Maye now vs. wait for Stafford" counterfactual to work at all. **An automated deterministic regression test for that exact scenario was attempted and not completed**: constructing a hand-rolled "N opponents have already picked" fixture requires exactly matching the real engine's pick-list-position-implies-draft-order contract (`_current_team()` reads `draft_order(profile)[len(picks)]`, not each pick's own `team_slot` field) — an early version of this fixture silently built an internally-inconsistent state and gave a misleading result, caught and discarded rather than reported as a false positive. Not re-attempted given the time already spent; flagged as real follow-up work, not fabricated as done.

## 3. Position-demand state — audited first, confirmed ALREADY EXISTS

Before building anything, audited `evaluate_cost_of_waiting_v2()` → `candidate_survival_probability()` → `_advance_cpu()` → `_select_asset()` → `_roster_need_adjustment()`/`_forced_position()`. **Real, already-shipped, roster-need-aware opponent behavior already exists**: `_roster_need_adjustment` gives a real, substantial bonus while a required starter slot is unfilled, and a real +18.0 penalty once a team already has more than its required QB/TE starters — a soft, probabilistic disincentive, never a hard exclusion (backups can still happen, exactly as required). Because `candidate_survival_probability()` already runs its Monte Carlo trials through this exact same real opponent-selection logic, **Make-It-Back already empirically reflects opponent positional demand** — no new "Position Demand State" module was built, matching the reuse-first rule.

**Verified empirically** (not just by reading code) with a correctly-constructed fixture (real draft-order-consistent picks, a mid-pack owner slot with real opponent turns on both sides): with 4 of 9 opponents already holding a starting QB, a mid-tier QB's survival probability to the owner's next turn was 0.14, vs. 0.06 when 0 of 9 opponents had one yet — real, correctly-directioned, modestly-sized (not exaggerated to a hard 0/1 by a broken first attempt, which was caught and corrected).

**Not built**: a compact position-demand UI summary (Section 4 of the original directive) — this data is already computable from real roster state via the same functions above; exposing it compactly in the UI is frontend work, out of scope for the reasons in the top-line summary.

## 4. News/alert infrastructure — Puka Nacua root cause found

Audited first: `redraft_external_intelligence_service.py` (already real, already exists — `current_alert`/`current_alert_severity` fields, UDK/FantasyPros identity-resolved overlay explicitly mentioning Puka Nacua by name in its own code comments as a team-code-mismatch case it already handles for OTHER fields).

**Root cause, confirmed by direct inspection of the real local file**: `current_alert` is sourced from `C:\NWR_DRAFT_DAY_TOOLS\KHA_FINAL_CHEAT_SHEET.csv` — a **static, manually-built local snapshot**, last generated **2026-09-02** (built by a separate, standalone tool, `build_kha_cheat_sheet.py`/`fetch_fantasypros_kha.py`, for the KHA draft day specifically), now 4 days stale. Puka Nacua's row IS present and correctly identity-matched (`position=WR, team=LA`) — but its `current_alert`/`current_alert_severity` fields are both genuinely empty strings in the source file itself. **Classification: `ALERT_STALE`** — not a join failure, not a filtering bug, not a UI rendering bug; the underlying local data source simply has no alert content for this player as of its last (4-day-old) build.

**Not fixed today**: `fetch_fantasypros_kha.py` makes real, authenticated calls to the FantasyPros paid API using the owner's own API key (`NWR_FANTASYPROS_API_KEY`) — re-running it uses the owner's real credential and quota. Not run without more explicit authorization, matching this session's standing discipline around real external-service actions. **Recommended**: re-run the existing build tool closer to tomorrow's real draft (mirroring the "Final Pre-Draft Refresh" pattern already established this session) — this is a real, disclosed, owner-actionable next step, not something to silently skip.

## 5. Draft board team-column bug — partial finding

The **legacy Draft Room** (`desktop/apps/redraft/src/pages.tsx`) already, correctly, computes its board grid from the real, live `teamCount` (`gridTemplateColumns: "38px repeat(${teamCount}, minmax(105px, 1fr))"`) — **no hardcoded "12" was found anywhere in this file.** `draft-room-v2.tsx` does not appear to have its own draft-board grid implementation at all yet (no `gridTemplateColumns`/board-grid pattern found there). **Could not reproduce or visually verify the reported "wraps at 12 columns" symptom** — this session cannot render the app. Flagged, not guessed at or "fixed" blind. Recommend the owner note exactly which view (`/` Legacy vs `/draft-room-v2`) showed the wrapping when reporting this again.

## 6-18. Draft Room consolidation, information architecture, search, queue, draft-action button, news card, sidebars, layout — NOT ATTEMPTED

Every one of these is real, legitimate, and clearly explained by the owner — the honest limitation is entirely on this session's side, not a judgment that the requests are wrong. This sandboxed session has no way to build the Tauri desktop app, render it, or interact with it visually — every frontend claim in this report would be unverifiable code written blind. Given the explicit, repeated instruction across both directives to not risk breaking tomorrow's real-draft fallback path, and given a real draft is tomorrow night, attempting a sweeping UI rewrite (tabs, sidebars, a new consolidated room, search, queue, a draft-action button, news cards) without any way to confirm it actually renders or works was judged the wrong call, exactly as in every prior UI request this session.

**What IS ready, for whoever does this work next** (a session with real build/render access, or the owner directly):
- The real backend fields this UI would need (Player Score, Team Score V1+V2 current/after/delta, Championship Equity V1+V2, Make-It-Back, Cost of Waiting, Pick Score, Raw Action Value/expected regret/decision-quality-percentile — now genuinely differentiated, evidence status, model versions) all already exist and are tested, via `redraft_decision_bundle`/`redraft_decision_bundle_v2`.
- The real pick-capture, undo, reset, search-adjacent (rapid capture with player search), and board mechanisms already exist in the legacy Draft Room (`pages.tsx`) and are real, tested, working today — a genuine feature-parity audit (V1 vs V2) should start from reading that file's real implementation, not guessing.
- The real position-demand signal (Section 3) is computable today from existing functions; a UI just needs to call and format it.
- The real news/alert mechanism (Section 4) exists; refreshing its data source is the one real action item, not a code change.

## Regression

Targeted re-check on the file most relevant to this pass (`tests/test_desktop_application_api.py`): 39 passed / 4 failed — the exact same 4 pre-existing baseline failures already documented this session, zero new failures. Full RAV/V2 suite: 22 passed. New regression fixture (mixed-position collapse): 1 passed, confirmed to fail against the pre-fix code.

## Final verdict

**`YELLOW_CONSOLIDATED_DRAFT_ROOM_NEEDS_FOLLOWUP`**

A real, credibility-critical backend bug is fixed and verified. Position-demand intelligence is confirmed already real and working — no wasted duplicate effort. A real root cause for the news gap is found and disclosed. The consolidated Draft Room itself, and every UI-facing item in both directives, remains **not started** — this is the honest, primary remaining gap, and it requires either a session with real frontend build/render capability or the owner's own hands-on implementation against the real, tested backend surface documented above.

No push. No merge. No deployment. No historical model tuning.
