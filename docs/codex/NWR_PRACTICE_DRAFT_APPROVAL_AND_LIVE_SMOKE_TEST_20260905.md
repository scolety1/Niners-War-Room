# NWR PRACTICE DRAFT — OWNER APPROVAL + LIVE LAUNCH — RECORD

Owner Spencer Colety explicitly authorized use of the currently admitted 2026 projection/current-data snapshot for **practice-draft operation only**, on 2026-09-05, distinct from and not modifying the prior 2026-09-02 real KHA draft approval.

## Approval mechanism used (existing, not invented)

1. **Archived, unmodified**, the real 2026-09-02 KHA draft-day approval + manifest + CSV to `%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\projections\2026\archive_2026_09_02_kha_draft_day_approval\` before touching anything — that historical record is preserved exactly as it was, not edited.
2. Authored a new, narrowly-scoped approval receipt (`admission_scope: "NWR_PRACTICE_DRAFT"`, `approved_by: "Spencer Colety (owner, explicit in-session practice-draft authorization, 2026-09-05)"`, `valid_until: "2026-09-05"` — temporary, today only, per the owner's own instruction), bound to the **identical, unchanged** `source_sha256` (`e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25`) already installed — no projection values, formulas, or model weights changed.
3. Installed it via the real, existing `redraft_engine_v1_service.install_projection_snapshot()` function — full validation, no bypass, no weakening of the approval system. Verified this is the SAME primitive the app's own bundled-seed auto-install already uses.
4. Re-verified against the real store, read-only: `require_manifest=True` ranking generation now returns 530 players, zero errors (previously: `('Projection approval receipt has expired.',)`).

**Explicitly not done**, per the owner's scope: no historical calibration data touched, no frozen Team Score artifact modified, no model retrained, no sealed/protected historical data touched, the real KHA draft-day approval was not modified or extended, nothing pushed/merged/deployed.

## Team Score implementation in use

```
TEAM SCORE IMPLEMENTATION IN USE:
shadow_numeric_authorities_service.team_score() — the existing, live, unmodified
production formula (DecisionBundle provenance label "team-score-v2")

WHY:
KHA is a 16-team league; the newly-frozen F4 model was validated only at 4-team
historical scale, while this live formula self-calibrates to any real team_count
via genuine Monte Carlo simulation — the overnight decision is honored unchanged.
```

## Live smoke test (real installation, real data, never the synthetic rehearsal)

Ran against the real local NWR installation, using a **brand-new profile** duplicated from the existing "2026 KHA High Stakes League — TEST" profile: **"2026 KHA High Stakes League — PRACTICE 20260905"** (`profile_id: 16d2e55044f64b1891e57c7481d18723`). The real KHA draft profile (`fb1c49402c7644a99120197d41344bbb`, 157 real picks) was read once for a before/after safety check and never mutated.

| Step | Result |
|---|---|
| 1. Start a fresh practice draft | ✅ New profile created and activated |
| 2. Load intended league configuration | ✅ 16 teams, full PPR confirmed |
| 3. Set/select draft slot | ✅ Verified with both slot 9 and slot 1 |
| 4. Generate recommendations | ✅ 8 real candidates, 2.08s latency (FAST preset; first call of the session, includes one-time comparable-league simulation — well within a draft clock) |
| 5. Record one opponent pick | ✅ Confirmed via the natural CPU auto-advance sequence |
| 6. Confirm player disappears from available pool | ✅ Confirmed directly |
| 7. Record one owner pick | ✅ Christian McCaffrey recorded |
| 8. Confirm owner roster updates | ✅ Roster size 1 |
| 9. Confirm recommendations recalculate | ✅ Roster-state hash changed |
| 10. Confirm Cost of Waiting updates | ✅ Present on every candidate |
| 11. Confirm Team Score updates (approved implementation) | ✅ Confirmed, using `team-score-v2` (the live, unmodified formula) |
| 12. Undo the owner pick | ✅ Removes exactly the chronologically last pick |
| 13. Confirm state restores correctly | ✅ Confirmed |
| 14. Reset the practice draft | ✅ Clean restart |
| 15. Confirm clean initial state | ✅ Confirmed |
| **SAFETY: real KHA board unchanged throughout** | ✅ **157 picks before, 157 picks after — byte-identical** |

Two sub-steps (5 and 13) initially failed on a flawed test-scenario construction on my part (attempting a contrived "owner picks last" restart, and expecting undo to target "the owner's pick" specifically rather than the chronologically last pick, which is undo's correct, intended behavior) — re-verified cleanly against the original scenario immediately after; not product issues. Full detail: `.codex-tmp/practice_approval_step4_smoke_test_results.json`.

## Current data check

| Field | Value |
|---|---|
| Snapshot source_sha256 | `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25` |
| Source/as-of (veterans) | 2026-08-08 |
| Source/as-of (rookies, excluded) | 2026-07-30 (independently stale; 78 rows excluded, unchanged from before tonight's approval) |
| Ranked player count | 530 (608 total in file; 78 blocked) |
| League configuration | 2026 KHA High Stakes League — PRACTICE 20260905 (16 teams, full PPR, 1QB/1RB/1WR/1TE/2FLEX/1K/1DST/4 bench, 12 rounds) |
| Draft slot | Configurable at start; verified with slots 1 and 9 |
| Team Score version | `team-score-v2` (live provenance label; underlying function `shadow_numeric_authorities_service.team_score()`) |
| Player Score version | `redraft_engine_v1_service.generate_rankings` (`MODEL_FAMILY=R2_FLEX_AWARE_REPLACEMENT`) |
| Cost of Waiting version | `evaluate_cost_of_waiting_v2` |

No live news, injury status, or player data was fabricated — everything above reflects exactly what the real, already-approved snapshot contains.

## Verdict

**`GREEN_PRACTICE_DRAFT_READY`**
