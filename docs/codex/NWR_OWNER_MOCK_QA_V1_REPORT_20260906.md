# NWR OWNER MOCK QA V1 — GET THE KINKS OUT

**Verdict: `YELLOW_SPECIFIC_KINKS_REMAIN`.**

Two real, concrete implementation bugs were found and fixed. Everything else the mocks exercised worked correctly. One separate, real governance-expiry finding was uncovered and disclosed but deliberately not fixed (requires owner authorization for a committed artifact). No historical model was tuned.

## 0. Setup

- Practice profile used: **"10-team 1QB Standard"** (`4b4a990faf124ce7a5d612537ba5943b`) — a real, pre-existing, empty profile on the owner's real local install. Never touched: KHA (already drafted), KHA Practice, Fantasy Gamers (real, pending Sleeper draft), KHA Test.
- Upgraded it into a realistic practice league for today's purpose: added real K (1) / DST (1) roster slots, enabled `practical_mode` (see Section 2), and populated its manual-asset pool with the same real 78 DATA_LIMITED rookies + 43 K + 32 DST already used by other real profiles — so it now exercises the full real player pool shape, not an artificially thin one.
- Practice-draft data governance already valid (renewed earlier today through 2026-09-09).
- The board was backed up before any mock and reset to a clean, empty state after both mocks — ready for the owner to use.

## 1. Mock #1 — normal draft (10 rounds, real local install)

Full output: `NWR_OWNER_MOCK_QA_V1_MOCK1_OUTPUT_20260906.txt`.

- Ran cleanly end to end: 10 real picks, real recommendations recalculated every round, zero crashes.
- Latency: 1.10s–2.92s per recommendation (mean 1.9s). All comfortably under a real draft clock; two rounds exceeded 2s (Section 11's flag threshold) — see Section 6.
- **2 real findings, both classified `MODEL_BEHAVIOR_TO_MONITOR`, not bugs** (investigated, not just asserted):
  - Team Score plateaued at 90.0 for two consecutive rounds after real picks. Investigated: `populationSize: 20` in the comparable-league population — once a roster already beats 18/20 comparable rosters, a percentile ceiling effect is mathematically expected, not a stuck calculation. Confirmed the underlying `rosterValue` (809.88) is real and distinct, not frozen; only the coarse percentile plateaus.
  - Several rounds showed Pick Score exactly tied at 100.0/50.0/0.0 across multiple different candidates. Investigated the real formula (`pick_score()` in `shadow_numeric_authorities_service.py`): `relative_score` is a **min-max normalization of Championship Equity win-probability across only the candidates evaluated in that one call** — the best candidate is always forced to exactly 100, the worst to exactly 0, regardless of how small the real underlying spread is. At the FAST preset's low trial count, many candidates' win probabilities land on the same few discrete values, producing exact ties. This is a **real, pre-existing structural property of the live Pick Score formula** (not introduced today) that mechanically explains this program's own historically-documented "close-call low resolution" finding — worth monitoring, not something to recalibrate today.

## 2. Between mocks — real bugs found and fixed

1. **`IMPLEMENTATION_BUG` (fixed)**: `update_redraft_profile()` had no way to enable `practical_mode` on an existing or manually-created profile — that flag was previously settable ONLY inside the Sleeper-import code path. Any profile built by hand (every ESPN league, since ESPN has no live-sync import in this codebase) that rosters K/DST as real starters would hit a hard wall: ranking generation fails outright, because K/DST are never part of the ranked universe by design and Practical Mode is exactly the flag that tells replacement-level calculation not to expect them there. **Reproduced directly**: adding K/DST slots to the QA profile without this flag failed with `REDRAFT_RANKINGS_UNAVAILABLE`. **Fixed**: `update_redraft_profile()` now accepts an optional `practical_mode: bool | None = None` (omitted preserves the existing value — fully backward compatible). **This is directly relevant to tomorrow's real ESPN league setup.**
2. **`UI_USABILITY_BUG` (fixed)**: the error above gave zero indication of its real, fixable cause — just "The active Redraft ranking is unavailable." Now includes the real, already-disclosed validation message (e.g. "Projection universe cannot support profile replacement depth: K 0/11, DST 0/11"). These messages never carry a filesystem path or other sensitive detail.
3. **`CURRENT_DATA_BUG` (found, disclosed, NOT fixed today)**: the repo's own bundled Redraft projection seed governance receipt (`docs/hq/model/.../NWR_DATA_GOVERNANCE.json`) has a real `valid_until: 2026-08-29` — already expired. Traced this directly as the root cause of the pre-existing `test_validate_admitted_redraft_2026_combined.py::test_combined_governed_snapshot_installs_and_validates` failure, and it plausibly explains a real slice of the broader ~324 pre-existing test-suite failure count. **Not renewed** — it's a committed governance artifact, and renewing it requires the owner's real authorization the same way the local install's own practice approval did earlier today, not something to do unilaterally. Flagged for the owner's decision.

Focused tests added for fixes #1/#2: 4 new tests, all passing (`tests/test_redraft_profile_practical_mode_toggle.py`). Full regression re-run clean: 3869 passed / 324 failed / 71 skipped — 324 is bit-for-bit the established baseline; the +4 is exactly this pass's new tests. Zero regressions.

## 3. Mock #2 — stress/abuse test (real local install, after fixes)

Full output: `NWR_OWNER_MOCK_QA_V1_MOCK2_OUTPUT_20260906.txt`.

| Check | Result |
|---|---|
| Real DATA_LIMITED rookies visible (correct field: `manualAssets`, not `boardCells`) | ✅ all 78, correctly authority-labeled, no fabricated scores |
| Real manual K/DST visible | ✅ all 75 (43 K + 32 DST), correctly labeled `MANUAL — NOT MODELED BY NWR` |
| Forced early-QB round | No QB in the FAST-preset top-8 at pick 1 — expected market behavior (RB/WR rank above QB early), not a bug |
| Forced 5-round RB run | Position counts climbed 2→3→4→5→6, no pathological explosion, no illegal state |
| No duplicate players on roster after 6 real picks | ✅ |
| Deliberate "wrong pick" + undo | The single most recent pick is what gets undone — correctly restores exact prior state for that one pick. **Real usability note, not a bug**: in MOCK mode the CPU auto-advances several picks after every owner pick, so "undo my last real pick" specifically requires as many undos as CPU picks happened since — this only affects solo MOCK practice, never a real live/Sleeper/ESPN draft (which never auto-advances; every pick there is entered one at a time, so "undo" always means the owner's own last action). Classified `UI_USABILITY_BUG` / documentation-only, not a code defect. |
| Repeated undo past pick zero | ✅ never crashes, returns a real "no pick to undo" state |
| Reset (`start_redraft_draft_room` again) | ✅ produces a clean board |

No illegal roster, no NaN/null, no impossible Make-It-Back value, no drafted-player-still-recommended case, no cache contamination observed across either mock.

## 4. Latency

| Metric | Value |
|---|---:|
| Mock #1 mean | 1.9s |
| Mock #1 max | 2.92s |
| Mock #2 mean | 1.6s |
| Mock #2 max | 2.11s |
| Calls over 2s (Section 11 flag threshold) | 3 of 16 total calls across both mocks |

All three slow calls were early-round cold-cache calls (the comparable-league Monte Carlo population had not yet been built/cached in that process). No call exceeded ~3s; every real Sleeper/ESPN draft clock this owner uses is measured in tens of seconds, so this is comfortably usable as-is. **Not optimized further today** — the mission's own threshold is a flag for investigation, not an automatic fix requirement, and the actual numbers stayed well within a usable range; further latency engineering would only be worth it if the owner reports the live app itself feeling slow.

## 5. Owner disagreement review

Not applicable this pass — both mocks used scripted, deterministic pick selection (there was no live human clicking through the actual Tauri UI during this session) rather than a real interactive owner session. Every real pick recorded was NWR's own top recommendation (Mock #1) or a deliberately-forced position choice (Mock #2), so there is no real disagreement to report. If the owner runs an interactive session on this same profile today, this section should be filled in with real disagreement data using the same fields this report's underlying prospective log already captures (Player Score / Team Score before-after-delta / Pick Score / Make-It-Back / evidence status for both NWR's choice and the owner's actual choice).

## 6. Prospective logging

Every decision from both mocks was logged to the real install's own `prospective_decision_log/4b4a990faf124ce7a5d612537ba5943b/decisions.jsonl` — practice logs are automatically separated from any real league's logs purely by profile_id namespacing (no shared file, no cross-contamination possible by construction). Not used to train or retune anything.

## 7. What was NOT done today

- No interactive human-in-the-loop session (see Section 5).
- No deep dive into how many of the ~324 pre-existing test failures share the expired-bundled-seed root cause (Section 2, finding 3) — flagged, not chased, per this mission's explicit scope.
- No frontend/UI verification (this session cannot render the Tauri app) — everything above was verified through the real backend/facade layer the UI actually calls, not a parallel harness.

## Final verdict

**`YELLOW_SPECIFIC_KINKS_REMAIN`**

Two real, concrete implementation bugs were found and fixed today (Practical Mode toggle gap, opaque error message) — both directly relevant to setting up tomorrow's real ESPN league correctly. One real governance-expiry issue was found and disclosed, correctly left for owner authorization rather than fixed unilaterally. Everything else exercised across two full mock drafts — recommendations, recalculation, position caps, undo, reset, DATA_LIMITED/K-DST visibility, latency — worked correctly. No historically-validated model was touched.

No push. No merge. No deployment.
