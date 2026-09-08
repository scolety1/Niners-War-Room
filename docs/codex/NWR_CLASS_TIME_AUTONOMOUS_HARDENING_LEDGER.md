# NWR Class-Time Autonomous Hardening — Running Ledger

**Started:** 2026-09-08, HEAD `00446dcd`. Owner unavailable (in class); explicit authorization for ordinary, reversible, local work only. No push/merge/deploy. No destructive real-board operations.

This ledger is updated after each coherent unit of work (per the directive's own checkpoint discipline) rather than producing a final report only at the end. Both real boards (403 `4b4a990faf124ce7a5d612537ba5943b`, Fantasy Gamers `4c5f04762921420595e4d8c7cda76582`) are re-verified byte-identical before and after every unit.

## Section 1 — DecisionBundle latency, continued

Reprofiled after the two fixes already committed (`00446dcd`). Real wall time (3 repeated calls, same isolated real 530-row profile): **5.81–6.95s** (down from the pre-fix ~13.4s, and down further from the first post-fix reading of 8.25-8.94s — real system-load variance between runs, both readings real and reproducible for their own run).

Real remaining hot path (cProfile, cumulative): `_select_asset` (10,056 calls, ~6.1s own time, down from 9.2s) → dominated by `_seeded_unit` (4.8M calls, ~3.7s, a real per-candidate SHA256-based deterministic jitter -- NOT touched, changing its algorithm would alter real shipped reproducible values) and the per-call roster `Counter` rebuild (`state["picks"]` is a full list rebuilt fresh every call by design -- restructuring this to an incrementally-maintained roster would require changing `_advance_cpu`'s calling convention, a real, riskier structural change, not a pure performance fix).

**Disposition: stopping here for this pass, per the directive's own "do not force a risky rewrite" instruction.** Target `<5s` not fully reached (currently ~5.8-6.95s); stretch `2-3s` not reached. No further changes made — the two committed fixes remain the full extent of this pass's latency work. Documented, not overclaimed.

## Section 2 — Shared-FLEX / deep-bench marginal utility fix (DONE, commit `4ba8ce00`)

Fixed the real, previously-reproduced bug: `roster_composition_report`'s `position_redundancy` credited each FLEX-eligible position its own independent FLEX allowance, double-counting the one real shared FLEX slot. Fix: derive redundancy directly from `starters` (the real, already-computed, shared-FLEX-aware greedy selection) instead of an independent capacity formula -- lossless by construction, no magic per-position bonus. 1 new regression test reproduces the exact real contention case (3RB/2WR/2TE/1FLEX) and proves TE redundancy is now correctly 1, not 0. Full regression: 53/53 (shadow_numeric_authorities) + 185 passed broader (same known 5 baseline). Frontend clean. Boards unchanged.

## Section 3 — Rerun leakage-clean validation (the FLEX fix changed live-ordering inputs) (DONE)

Reran the same leakage-clean 48-paired-draft protocol (unchanged gates). **Result: mean_delta +91.78 (vs +92.49 pre-fix, real small variance), wins 32/48 (67%, unchanged), no season regression >5%. ALL 3 GATES STILL PASS.** The FLEX fix only affects rare 3rd-deep-bench scenarios and does not materially change the promoted engine's validated real performance. Promotion remains KEPT, no rollback needed.

## Section 4a — Diggs-class acquisition-filter fix (DONE, this commit)

Full evidence: `docs/codex/NWR_DIGGS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`. Widened
`build_current_projection_candidate`'s universe filter from `last_season==season` to
`last_season.between(season-1, season)` (Diggs-class: real active players whose most recent
recorded stat line lags one season). Real audit against the exact live-build snapshot caught a
genuine false-positive risk (Philip Rivers/Russell Wilson, `status=ACT` despite real retirement)
-- fixed with a second, real, gsis_id-keyed cross-check against the already-staged
`seasonal_rosters_2025` snapshot (excludes only the newly-widened slice, only when real roster
status is INA/RET/CUT, keeps unmatched gsis_ids). **Final guarded result: 910 -> 973 (+63 net),
12 real false positives caught and excluded, 75/75 (100%) roster-snapshot coverage on the
widened slice.** Also fixed a genuine pre-existing latent empty-DataFrame `KeyError` in
`blocked_frame`/`identity_frame` construction, first reachable via this new exclusion path. 4
new tests (true-positive, true-negative, unwidened-slice-untouched, missing-coverage-kept), all
pass; full 77-test regression across the 3 touched files clean. Both real boards re-verified
byte-identical.

## Section 4b — Brooks-class fix (DONE, this commit)

Full evidence: `docs/codex/NWR_BROOKS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`. Reuse-first search
found `redraft_2026_rookie_projection_model_service.py`'s already-validated position+round
rookie-year cohort model (previously scoped only to the current draft class); renamed its two
private helpers (`cohort_projection`, `median_stats`) to public and added
`build_insufficient_history_fallback_candidate()` reusing them for the general "current, active,
real draft capital, insufficient own history" category (real count: 173 blocked, 66 with real
draft capital, 38 from 2023-2025 classes). Real historical spot-check (168 real cases, real
sophomore outcomes): **honest negative result** -- the cohort-median challenger LOSES to a naive
zero baseline on aggregate MAE (16.79 vs 9.80, wins 28/168) because the real zero-rookie-games
population is bust-dominated. Per "if weak, say so": **not promoted as a calibrated point
estimate**; kept strictly additive/review-only, solving real invisibility (Top-250
coverage/search/compare) rather than claiming point-accuracy. Never wired into Pick
Score/RAV/ordering. 4 new tests pass; full regression across both touched files (18 tests) clean
(1 known pre-existing unrelated manifest-hash failure confirmed present on unmodified HEAD too).
Both real boards re-verified byte-identical.

## Section 4c — Top-250/real-market coverage rerun (DONE)

Full evidence: `docs/codex/NWR_TOP250_COVERAGE_RERUN_V1_20260908.md`. Owner's local ADP
snapshot proved unsuitable (league-specific, pre-matched, doesn't contain Diggs/Brooks at
all); used the real, already-admitted FFA 2026 market pack instead (220 real QB/RB/WR/TE
rows). **Result: 216/220 (98.2%) FULLY_MODELED**, every previously-identified SOURCE_GAP name
now covered. 4 remaining real gaps individually root-caused: Marvin Harrison Jr. is a
diagnostic-script-only false negative (real production pipeline resolves him correctly via
PFR-ID bridge); Kenneth/Kenny Gainwell and Chigoziem/Chig Okonkwo are real nickname-vs-
registry-name variants (players ARE in the universe under their registry name); Joe Mixon is
a real, deliberately-unopened `RSN` status-code exclusion. No code change this unit.

## Section 5 — Judkins/role-change blind-spot experiment (DONE, reference-only)

Full evidence: `docs/codex/NWR_JUDKINS_ROLE_CHANGE_BLIND_SPOT_V1_20260908.md`. Judkins never
manually changed. Real finding: he's already FULLY_MODELED with substantial real 2025
rookie-year volume (230 carries, 827 yards, 14 games); NWR projects 154.8 pts vs FFA's real
185.0 (~16.7% gap). Root mechanism verified: `_project_persistence` carries the player's own
prior-season real games total verbatim (14) rather than assuming a healthy 17-game season --
a real games-availability artifact, not clearly a role-change-specific signal. No real current
2026 preseason depth-chart/role source is available yet (season hasn't started) to build and
calibrate the directive's proposed role-disagreement feature without effectively substituting
market ADP as the answer target (explicitly disallowed). Per the directive's own sanctioned
fallback: left REFERENCE-ONLY, no code change, Player/Team Score/Pick Score untouched. The
real, distinct games-persistence question surfaced is flagged as a separate future follow-up.

## Section 6 — Status/risk live intake path (DONE, backend; frontend flagged remaining)

Full evidence: `docs/codex/NWR_STATUS_RISK_INTAKE_PATH_V1_20260908.md`. Real gap: the intake
CONTRACT (`add_verified_status_override`) and its READ side were both already real and
already wired live, but the WRITE side had no facade/HTTP/GUI entry point -- only a hand-edit
of the committed JSON file. Added `list_player_status_overrides()` and
`submit_player_status_override(...)` to `DesktopBackendFacade`, wrapping the existing
contract as-is (honest note: the real taxonomy is SEASON_OUT/NOT_WITH_TEAM/TEAM_CORRECTION,
not the richer 9-value list the directive's own text assumed -- built on the real one, no
fabricated kinds). 5 new tests pass (isolated fixture config, never the real committed file);
22-test regression across related files clean; known 5-test baseline unchanged. Compact
frontend form flagged as the remaining step, not built this pass (time budget).

## RESUME STATE (checkpoint after section 6, before starting section 7)

- Branch: `work/nwr-draft-upgrade-hq-v1-20260903`. HEAD: `e336e7ce`. Worktree:
  `C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq`.
- Dirty (pre-existing, NOT this session's work, left untouched throughout): 5 files under
  `docs/model_v4/*.md` (already modified at session start, unrelated to this directive).
- Sections 1-6 DONE and committed (`4ba8ce00`, `40a84565`, `37ddf29f`, `1b65517e`,
  `4031a021`, `e336e7ce`). Both real boards (403 `4b4a990faf124ce7a5d612537ba5943b` sha256
  `ba106a0c...`, Fantasy Gamers `4c5f04762921420595e4d8c7cda76582` sha256 `9a2af611...`)
  reverified byte-identical after every commit.
- Known, unchanged baseline: `test_desktop_application_api.py` has exactly 5 pre-existing
  failures (see `nwr-draft-upgrade-hq-baseline-failures` memory); do not treat as new
  regressions.
- Next exact command: begin Section 7 (Ballers import workflow) by searching existing
  repo infrastructure for a Ballers PDF/CSV parser (per earlier-session "Ballers PDF
  pipeline" work referenced in project memory) before building anything new.
- No push/merge/deploy/destructive-real-board operation performed or planned.

## Section 7 — Ballers import workflow (DONE, backend; frontend flagged remaining)

Full evidence: `docs/codex/NWR_BALLERS_IMPORT_WORKFLOW_V1_20260908.md`. Found substantial
existing infra (CSV+PDF parsers, additive per-position persistence, single load point already
used by all consumers). Closed real gaps: wired PDF import to the facade (previously
unreachable), added real per-position version history + rollback (previously nonexistent),
enriched preview with perPositionCounts/duplicateRows. Found+disclosed (not fixed, out of
scope) a real pre-existing, unrelated fixture-drift bug: the bundled governed-snapshot test
fixture other tests already depend on now fails with "no rankable player rows" even
unmodified, likely a source_as_of freshness-window drift as simulated "today" advances. 10 new
tests pass; 65-test regression across 3 files clean; known 5-test baseline unchanged.

## Section 8 — Ballers K/DST pipeline readiness (DONE, verification only)

Full evidence: `docs/codex/NWR_BALLERS_KDST_READINESS_V1_20260908.md`. Found the directive's
schema/matching/labeling requirements were already satisfied by existing infra (K/DST are
first-class positions in the rich UDK schema, DST-team/K-identity matching already real and
tested, storage fully additive and never overwrites canonical state) plus this session's own
Section 7 additions (which apply generically, no K/DST-specific path). Added 1 confirming test
proving K/DST get the full schema + versioning/rollback automatically. No new production code.

## Section 9 — K/DST direct model research baseline (DONE, NOT promoted)

Full evidence: `docs/codex/NWR_KDST_DIRECT_MODEL_RESEARCH_V1_20260908.md`. Built real,
disclosed K/DST scoring formulas (nflverse computes neither) and real walk-forward-evaluated
OLS baselines from real weekly FG/PAT and defensive-event + schedule data. Caught and fixed a
real methodology bug in the first pass (regressing a season's score on that same season's own
concurrent stats -- trivially near-perfect, not a real prediction test); corrected to real
prior-season -> next-season framing. **Honest result: both K and DST direct models beat a
naive persistence baseline on MAE but are WORSE rankers (lower Spearman) than just repeating
last year's total** -- real, weak, consistent (low per-season variance) signal. Per "if weak,
say so": NOT promoted; Ballers/UDK remains the valid K/DST source. Real missing-features list
disclosed for a future session.

## Section 10 — K/DST timing dynamic-policy stress test (DONE, no code change)

Full evidence: `docs/codex/NWR_KDST_TIMING_STRESS_TEST_V1_20260908.md`. Ran all 8 directive-
named scenarios via direct `_forced_position`/`_roster_candidate_allowed` calls. Confirmed:
deadline scales correctly with real round count regardless of team count/bench depth; K/DST
never forced early just because starters finished early; K2/DST2 structurally impossible
outside an explicit experimental multi-K/DST format; a real market-ADP pathway exists for
K/DST to rationally move earlier, correctly labeled MANUAL_UNMODELED. Two real, honest
findings disclosed (not fixed, not bugs against documented design): opponent/pool-scarcity
signals have zero effect on this team's own timing (per-team policy only); under extreme
multi-position scarcity, skill-position priority can sacrifice K/DST entirely even on the
literal last pick.

## Section 11 — Pick Score secondary sort external validation (DONE, no adjustment)

Full evidence: `docs/codex/NWR_PICK_SCORE_TIE_ORDER_VALIDATION_V1_20260908.md`. Built 3 real
DecisionBundles (8/12/16-team, varying roster fullness), measured real pairwise pick_score
ties and whether raw_decision_utility resolves them. Real, honest result: 778/1038 real ties
across cases, resolution rate ranges 0-81% depending on real candidate differentiation (a high
double-tie rate among similar deep-bench candidates matches the tertiary player_id key's own
documented purpose, not a defect). Marginal-utility promotion (this session's own separate
work) changed row-1 in 2/3 cases, corroborating the walk-forward promotion evidence. No harm
found; no adjustment made.

## Section 12 — Pair-turn planner GREEDY vs JOINT decision analysis (DONE, kept informational)

Full evidence: `docs/codex/NWR_PAIR_TURN_PLANNER_GREEDY_VS_JOINT_V1_20260908.md`. Compared
real GREEDY (sequential top-1 x2) vs real JOINT (evaluate_pick_pairs) at the 3 directive-named
turn slots, starting from real valid partial-mock states. Pair composition differed in 1/3
cases; in that case JOINT improved win probability (+0.025) but team_score percentile
collapsed 90.0->28.3 -- a real, concerning disagreement between the two real scoring metrics
that could mean genuine unsafe win-probability-only optimization or Monte Carlo noise at this
trial count; the small sample can't distinguish which. Per "if not [safe], keep it
informational": NOT promoted. No code change.

## Section 13 — FFA Sept-4 outlier/role audit

(next)
