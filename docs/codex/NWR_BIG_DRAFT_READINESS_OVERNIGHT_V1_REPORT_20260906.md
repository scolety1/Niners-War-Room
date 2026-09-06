# NWR BIG-DRAFT READINESS — OVERNIGHT REPORT

**Real draft tomorrow night. Verdict: `YELLOW_BIG_DRAFT_READY_WITH_KNOWN_LIMITATIONS`.**

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
