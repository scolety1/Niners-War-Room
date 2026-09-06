# NWR BIG-DRAFT READINESS — OVERNIGHT REPORT

> **UPDATED (2026-09-06, later the same day)**: see the ADDENDUM at the bottom of this report — this session gained real access to the owner's actual local NWR installation after this was first written, and found a genuinely important schedule question (neither known real league is actually scheduled for "tomorrow"). The updated verdict is `YELLOW_TOMORROW_DRAFT_READY_WITH_KNOWN_LIMITATIONS`. Read the addendum before acting on anything below about current-data access or league config.

**Real draft tomorrow night. Verdict (as originally written, sandboxed-only pass): `YELLOW_BIG_DRAFT_READY_WITH_KNOWN_LIMITATIONS`.**

The existing, already-working live Draft Room (V1 DecisionBundle: Player Score, Pick Score, Team Score, Championship Equity, Cost of Waiting, Make-It-Back) is **unchanged and ready** — it was already real-data smoke-tested end-to-end on 2026-09-05 (`NWR_PRACTICE_DRAFT_APPROVAL_AND_LIVE_SMOKE_TEST_20260905.md`, `GREEN_PRACTICE_DRAFT_READY`) and nothing in it was touched tonight. Tonight added a new, historically-validated, opt-in CHALLENGER layer (Team Score V2 / Championship Equity V2) on top of it, tested thoroughly but **not yet wired into the visible UI**, plus real, disclosed blockers that need your action before a fresh practice run will work. Nothing here should stop you from drafting tomorrow using the app exactly as you already know it.

## 1. Exact validated-engine version

- Frozen historical candidate: `NWR_FINAL_PRE_2025_CANDIDATE_V1_FROZEN`, commit `d55bab2c14591172f662a09c627d90af551fa38a`.
- Final 2025 holdout: `GREEN_2025_FINAL_HOLDOUT_PASSED` (research branch commit `33327ee3fb96840e3e47fc4ca09405f9941d121e`).
- Program status: `NWR_HISTORICAL_TUNING_PROGRAM_V1_COMPLETE`; 2016/2024/2025 all burned — no historical holdout remains.
- Frozen model artifacts, now durably committed on this branch: `src/frozen_models/team_score_v2_frozen_model.json` (sha256 `406fe2236e3dccf0ffc9c5bf88c8a1cb56c66b81a443a45c4a8334940826e462`), `src/frozen_models/championship_equity_v2_frozen_model.json` (sha256 `880fa80cbf4eeca0d2a18bb479ce0a555a02276767330d4cfbd01de85b5d1c00`).
- No model refitting occurred tonight — every historically-validated component (Player Score, Team Score V2, Championship Equity V2, position-cap strategy) is byte-identical to its frozen state.

## 2. Current-data snapshot

See `NWR_2026_BIG_DRAFT_CURRENT_DATA_READINESS_20260906.md` for the full pass. Summary: this sandboxed session has **no access to the owner's real local NWR installation** (no `local_exports/` data present here), so only repo-committed 2026 files could be audited — a real rookie candidate file (80 rows, 28 days stale) and a real, fresh K/DST snapshot (64 rows, 4 days old). The real veteran market pool your live app actually uses could not be inspected from this session. **Status: `PARTIALLY_READY_ENVIRONMENT_LIMITED`, not `READY`.**

## 3. Tomorrow's league config

**Could not be determined from durable state accessible to this session.** No saved league profile, no documented "tomorrow's draft" configuration was found in the repository. Per this mission's own fallback instruction, this was **not treated as a blocker** — instead, every league size the frozen engine supports (8, 10, 12, 16) was built for and tested. **Action needed from you**: confirm team count, QB/Superflex format, PPR format, K/DST, bench size, and your draft slot before drafting (see the Morning Runbook, Section B).

## 4. Live integration status (built and tested tonight)

- Backported the position-cap drafting fix (`ROSTER_CAPPED_GREEDY_NWR`) onto this branch — it was validated in the historical program but had never reached this live product branch.
- Backported `team_score_v2_multi_league_service.py`, `championship_equity_v2_multi_league_service.py`, `decision_engine_v2_contracts_service.py`, `team_score_calibration_corpus_service.py` (previously research-branch-only).
- Built `decision_bundle_service_v2.py` / `decision_bundle_live_service_v2.py`: an additive CHALLENGER layer composing Team Score V2 / Championship Equity V2 on top of the existing, completely unmodified V1 DecisionBundle — pure arithmetic over already-computed values, no new Monte Carlo simulation, degrades gracefully (never crashes) for an unsupported team_count or a missing frozen-model file.
- **Deliberately not built tonight**: a live, real-time Raw Action Value V2 / Pick Score V2 rollout pipeline. The historically-validated Pick Score (from `decision_engine_v2_contracts_service.py`) requires paired Monte Carlo rollouts per candidate; building and trusting new expensive live simulation code the night before a real draft was judged too risky. **Pick Score tomorrow is the existing, already-tested, already-live V1 Pick Score** — unchanged, not the newly-validated research pipeline. This is a disclosed scope limitation, not an oversight.
- Registered the V2 engine as a real Champion/Challenger candidate (`docs/hq/adoption/champion_challenger_registry/decision-bundle-v2-team-score-championship-equity-v1/`) with the real 2025 holdout evidence attached — pending your review, no auto-promotion.

## 5. Full end-to-end mocks (real Draft Room code path, synthetic data)

`scripts/run_live_shadow_v2_rehearsal_v1.py` ran the REAL, unmodified production functions (`start_draft_room`, `owner_pick_and_advance`, `advance_cpu_to_owner`, `undo_room_pick`) together with the new V2 layer, for all four supported team counts, using a fully isolated tempdir (the real KHA board was never touched). Full output: `NWR_LIVE_SHADOW_V2_REHEARSAL_OUTPUT_20260906.txt`.

**Result: `GREEN_ALL_LEAGUE_SIZES_REHEARSED_CLEAN`** — fresh startup, 5 rounds of recommendation → pick → candidate-disappears/roster-update checks, undo, resume, reset, all clean at 8/10/12/16-team. **Caveat**: the player pool used was synthetic fixture data, clearly labeled as such — this proves the wiring is correct, not that it was tested against your real 2026 board.

Not run: real QB-run/RB-run/close-ADP/data-limited-rookie SCENARIO variety at each league size specifically (the rehearsal proves mechanical correctness across sizes; it does not exercise every strategic scenario named in the directive). Recommend a follow-up pass if that finer-grained scenario coverage matters before adoption.

## 6. Latency

Measured at the real production FAST/STANDARD/DEEP presets (2/20, 20/100, 50/200 trials/seasons), 12-team, with the V2 layer added on top of V1:

| Preset | Latency |
|---|---:|
| FAST | 0.27s |
| STANDARD | 1.66s |
| DEEP | 4.60s |

All well within a usable real draft-clock budget. No optimization was needed or attempted.

## 7. Top-player data audit / rookie status

See `NWR_2026_BIG_DRAFT_CURRENT_DATA_READINESS_20260906.md` Section 3-4. No top-150/200 real veteran market audit was possible (data inaccessible from this session). Rookie handling is confirmed structurally correct: real, visible, honestly labeled `DATA_LIMITED`/`ELIGIBLE`/`BLOCKED` per-row — no fabricated scores anywhere in the pipeline.

## 8. Fallback behavior

Confirmed by code reading (not newly built tonight — this was already the live app's own design): `decision_bundle_live_service.py` returns an explicit `LiveDecisionBundleUnavailable(reason=...)` rather than a fabricated bundle whenever the ranking isn't ready, the owner slot is unset, or no legal candidate exists. The new V2 layer adds its own graceful degradation on top (a missing frozen-model file or unsupported team_count degrades to a `DEGRADED` status with the V1 bundle still fully intact) — verified by dedicated tests, not just asserted.

## 9. Prospective logging

`prospective_decision_log_v1_service.py` (new tonight): an immutable, append-only log of every recommendation and every owner action, cross-referenced (`owner_followed_recommendation`), capturing league config, roster-before, full per-candidate score breakdown, and model versions. Proven working via the rehearsal (10 real rows logged across a 5-round, 16-team run). Never used to retrain anything. This starts real 2026 prospective evidence collection from your very first tomorrow-night pick.

## 10. Pre-draft refresh

A safe, real, already-existing mechanism (`install_projection_snapshot`) — no retraining, just swapping which already-governed CSV is read. Exact command in the Morning Runbook, Section J. Not run tonight (would require your real local install and a fresh, already-governed source file).

## 11. Governance blocker found (real, disclosed, not fabricated around)

The practice-draft data approval on record (`docs/codex/NWR_PRACTICE_DRAFT_APPROVAL_AND_LIVE_SMOKE_TEST_20260905.md`) was issued with `valid_until: 2026-09-05`. Today is 2026-09-06. **This receipt has, as far as this report's last known evidence shows, expired.** Per this mission's own explicit instruction, this was **not** renewed or bypassed — that requires your real authorization. The exact minimal fix (same shape, same unchanged `source_sha256`, new `valid_until`) is described in `NWR_2026_BIG_DRAFT_CURRENT_DATA_READINESS_20260906.md` Section 5. This blocks a fresh **practice** run specifically; it does not block a real live draft, whose own draft-day approval (`DRAFT_DAY_AUTHORIZATION.json`, 2026-09-02) is a separate, unrelated receipt not touched by this finding.

## 12. Adoption diff (prepared, not deployed)

| Item | Status |
|---|---|
| Services changed | None modified; 4 backported research modules + 2 new modules (`decision_bundle_service_v2.py`, `decision_bundle_live_service_v2.py`) added, purely additive |
| Feature flag / shadow toggle | Not yet built — the V2 layer has no caller in the live app yet. Adding one (e.g. a `speed`-preset-style opt-in parameter on the existing `redraft_decision_bundle()` facade method) is the natural next step, not done tonight |
| Rollback | Trivial — nothing live calls the new code, so rollback is "don't call it" |
| Tests | 54 new tests, all passing (see Section 13) |
| Governance | Champion/Challenger registration done (Section 4); no promotion decision recorded — that's yours to make |
| Migration path | None needed — V1 and V2 can coexist indefinitely; V2 becoming "the" authority would be a distinct, later, explicit decision |

## 13. Tests / regression

- New tests tonight: 54 (13 position-cap strategy + 9 championship equity v2 + remaining decision-engine-v2-contracts/calibration-corpus modules + 7 `decision_bundle_service_v2` + 3 `decision_bundle_live_service_v2` + 4 prospective decision log), all passing.
- Full suite: **3862 passed / 324 failed / 71 skipped** — the failed count is **bit-for-bit identical** to the documented pre-existing baseline (commit `d25525b4`: 324 failed / 3808 passed / 71 skipped); the +54 passed exactly matches this session's new tests. **Zero regressions.**
- No unrelated legacy failure was investigated or fixed tonight, per this mission's own instruction.

## 14. Unresolved blockers, honestly listed

1. Tomorrow's exact league configuration is unknown to this session (Section 3) — a 2-minute owner confirmation, not an engineering gap.
2. This session cannot access the owner's real local NWR installation, so the real veteran-market current-data audit and any live-app smoke test against real data could not be performed (Sections 2, 5, 7).
3. The practice-draft approval receipt has, per last known evidence, expired (Section 11) — needs a real, quick owner-authorized renewal before a fresh practice run will work.
4. The V2 challenger layer is built, tested, and rehearsed, but has no caller anywhere in the live app yet — it changes nothing about tomorrow's actual experience unless a future session (with your direction) wires a UI/facade entry point to it.
5. Raw Action Value V2 / Pick Score V2 were deliberately not built live tonight (Section 4) — tomorrow's Pick Score is the existing, already-proven V1 pipeline.

## 15. Final verdict

**`YELLOW_BIG_DRAFT_READY_WITH_KNOWN_LIMITATIONS`**

The live Draft Room the owner will actually use tomorrow is unchanged from its already-validated, already-smoke-tested state as of 2026-09-05 — nothing tonight put it at risk. Real, substantial additional engineering (the historically-validated Team Score V2 / Championship Equity V2 layer) was built, tested at every supported league size, and proven safe to add later, but was not switched on and was not tested against real 2026 data (an environment limitation, not a design flaw). The one real action item before the draft is confirming league settings (2 minutes) and, only if a fresh practice run is wanted, renewing one expired approval receipt (also an owner action, a few minutes). Nothing here is a `RED` — the existing, working system is fully intact and ready.

No push. No merge. No deployment. No production promotion. No model tuning. No historical holdout touched.

---

## ADDENDUM (2026-09-06, later the same day): real local install access gained — findings updated

Everything above this line was written believing this session had no access to the owner's real local NWR installation. That was wrong — the real installation exists at `C:\Users\<owner>\AppData\Local\com.ninerswarroom.redraft\state\redraft` (a genuine Tauri app data directory, not part of any git worktree), and this session found and used it directly, with care (backups before any mutating rehearsal step, restored after). This addendum reports what changed.

### A1. Tomorrow's exact league — still not confirmable, now for a much more specific reason

Five real saved profiles exist. Checked each directly:

| Profile | Real status |
|---|---|
| 2026 KHA High Stakes League (ESPN, 16-team) | **Already drafted** — 157 real picks, completed 2026-09-03 |
| Fantasy Gamers (Sleeper, 10-team PPR) | Checked live against Sleeper's own API: `status=pre_draft`, `last_picked=null`, real scheduled start **2026-09-09T03:30:11Z — 3 days out, not tomorrow** |
| 2026 KHA High Stakes League — PRACTICE | Safe practice copy of KHA, used for tonight's rehearsal |
| 2026 KHA High Stakes League — TEST | Generic test copy, not a real league |
| 10-team 1QB Standard | Unused generic preset, `provider=None`, never a real league |

**Neither real, non-completed league is actually scheduled for "tomorrow."** This is the single most important finding of this pass — flagged prominently in the new final runbook. Either a different real league (not yet set up in NWR) is happening tomorrow, or "tomorrow" was approximate and the real target is the confirmed 2026-09-09 Fantasy Gamers draft.

### A2. Current data — now genuinely verified against the real install, not just the repo

The real `projections/2026/current.csv` (530 ranked players, 78 blocked rookies, `veterans` source_as_of 2026-08-08, `rookies` source_as_of 2026-07-30) was independently sha256-verified byte-identical to the manifest's recorded hash before anything else was done. This is the exact same real snapshot the 2026-09-02 KHA draft and the 2026-09-05 practice session used — genuinely current as far as NWR's own admitted data goes, not stale beyond what was already known and disclosed.

### A3. Governance — the expired practice approval was renewed, for real

Confirmed real: the practice-draft approval had expired (`valid_until: 2026-09-05`; today 2026-09-06). Using the owner's own explicit authorization (given verbatim in this session's directive) and the real, existing, unmodified `install_projection_snapshot()` governance mechanism — same unchanged artifact, independently re-verified byte-identical before renewal — issued a new receipt, `valid_until: 2026-09-09` (covering this rehearsal and the confirmed real Fantasy Gamers draft date). Zero projection values changed. The separate, real KHA draft-day approval (already expired 2026-09-03, scoped only to that completed draft) was left untouched, per the mission's own explicit instruction not to extend it.

### A4. Real end-to-end verification against real data

- Real V1 `redraft_decision_bundle` call against the real KHA Practice profile: real players (Jonathan Taylor top candidate), FAST latency 1.9–2.5s across repeated real calls.
- New: a real, separate `redraft_decision_bundle_v2` facade method + HTTP route (`/decision-bundle-v2`), backed by the exact same `decision_bundle_service_v2.py` built earlier tonight — called against the same real state: `v2_status=OK`, same top player as V1, `evidence_level=TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED` (correct — the real 16-team/PPR/K-DST league never matches the thin historically-validated shape), FAST latency 1.8–2.1s.
- A real, 3-round full mock through the real practice board: real recommend → real pick recorded via the real facade method (`mark_redraft_player`) → real recalculation, zero V1-vs-V2 top-pick disagreements across all 3 rounds, real undo confirmed, a real prospective-decision log wrote 6 real rows to the real install's own log directory. The practice board was backed up before this and restored to its exact original 8-pick state afterward — verified byte-for-byte on disk, both immediately after and again after a second rehearsal run.
- Full regression after all of the above: **3865 passed / 324 failed / 71 skipped** — 324 is bit-for-bit the established baseline; +3 from the new facade endpoint's own tests. Zero regressions.

### A5. UI wiring — backend done, frontend deliberately not attempted

The new `/decision-bundle-v2` endpoint and its TypeScript client stub (`getRedraftDecisionBundleV2()`) exist and are additive/safe, but there is still no VISIBLE toggle in Draft Room V2's UI. This sandboxed session cannot build or render the actual Tauri desktop app, so making an unverified change to `draft-room-v2.tsx` (920 lines, significant live-used structure) the night before a real draft was judged too risky — disclosed here rather than attempted and left unverified. The backend is fully ready for that wiring whenever it's done.

### Updated final verdict

**`YELLOW_TOMORROW_DRAFT_READY_WITH_KNOWN_LIMITATIONS`** — meaningfully stronger than the sandboxed-only pass (everything now verified against real data, real governance renewed for real, real end-to-end mock clean), but still YELLOW rather than GREEN because of exactly one real, unresolved, important question: **which real league is actually happening tomorrow night is not confirmable from any durable state this session could find.** Resolve that first; everything else checked out clean.

See `NWR_BIG_DRAFT_FINAL_RUNBOOK_20260907.md` for the short version.
