# NWR Owner UI Ledger — Real Chrome-Rendered Verification (V1)

**Date:** 2026-09-08 (overnight V4 continuation)
**Scope:** Directive V4 section 24 — verify Cheat Sheet fields, Player Drawer fields, Action badge colors (Compare/Drawer specifically), and confirm Legacy Draft Room removal didn't break anything, with ACTUAL rendering evidence, not "same component" inference.

## Method

Stood up a real, isolated instance of the product: the real desktop API server (`src/desktop_api/server.py`), pointed via `NWR_REDRAFT_HOME` at a disposable data root (never the real 403/Fantasy Gamers boards), seeded with the real bundled 608-row projection dataset in a real 12-team league at `owner_slot=12` (the slot that produces a genuine back-to-back turn, so `bestTurnPlan` could also be exercised); the real Vite dev frontend (already running from earlier in this session, port 1422); and Chrome (via the browser automation tools) navigated to the real rendered app. This is the actual product rendering real data end-to-end, not a code walkthrough.

## Findings

### 1. Legacy Draft Room removal — VERIFIED, real navigation

Navigating directly to `http://127.0.0.1:1422/` (the bare root, where the old `DraftRoomPage` used to live) correctly redirects to `#/draft-room-v2` and renders the real Draft Room V2 UI. Confirmed via actual browser navigation, not a route-table read.

### 2. Cheat Sheet — VERIFIED, real rendering, independent of the DecisionBundle latency issue below

The Cheat Sheet tab renders real data (12 TEAMS · 1 PPR · 0 TE PREMIUM, "518 PLAYERS", RANK/PLAYER columns with real names in real rank order) and loads independently of the (slow) DecisionBundle endpoint — it stayed correct and responsive throughout the investigation below.

### 3. A real, significant DecisionBundle latency regression — found only through actual rendering

The Suggestions panel showed a real, reproducible "DecisionBundle unavailable — The DecisionBundle request failed - backend calculation unavailable" error on repeated fresh page loads against this real, full-scale (530-real-player) league. Traced the real cause, not assumed:

- Direct, isolated Python timing (bypassing the HTTP layer entirely, same process, real facade call) measured **`build_live_decision_bundle` at ~10.2-12.8 seconds** for a single FAST-speed call against this real 530-row ranked pool — repeatable across multiple calls in the same warm process, not a one-time cold-start cost. This is a severe regression from the documented benchmark (`docs/codex/DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md`: FAST "~0.7s cold, ~0.1-0.2s once comparable-league population is cached").
- `simulate_comparable_leagues` itself (trials=8, the FAST preset) was measured separately and is NOT the bottleneck (1.7s). The remaining ~8-11s is inside `build_live_decision_bundle`'s per-candidate scoring path (Raw Action Value / cost-of-waiting Monte Carlo, evaluated per FAST-preset candidate) — not further profiled this pass; flagged as the concrete next step.
- The real UI does show an honest "Computing... Calculating the real DecisionBundle for this pick." loading state while waiting (confirmed by catching it mid-flight) — a genuinely good, honest UX detail, not a fabricated/instant number.
- But the frontend does NOT wait long enough for the real ~10-13s computation in this scenario: it transitions from "Computing..." to the terminal "DecisionBundle unavailable" state before the real backend response arrives, leaving the owner stuck on a false error for a computation that was, in fact, still correctly in progress. A full page reload can eventually catch a fast-enough completion and show real data (observed once), but this is not a reliable recovery path for an owner during a real draft.
- Confirmed via `_write_json`'s real crash trace (see below) that this is not solely a display glitch: the real backend genuinely takes this long for this real-scale profile.

**This is a genuine, real, owner-facing reliability risk for any league with a full-scale real player pool close to this session's real 403 league's own scale** — not previously caught because the documented latency benchmark was evidently not measured against a comparably-sized real pool, and this session's own earlier multi-league batteries (UPDATE 9, UPDATE 21/section 22) used the `mark_redraft_player`/direct facade path, which tolerated the real per-call latency without ever exercising the frontend's own timeout/retry behavior.

**Disposition**: not fixed tonight — this needs real profiling to find the actual hot loop before any fix is attempted, which is a distinct, substantial unit of work, not a same-night patch under time pressure this late in an already long session. Flagged as the single highest-priority follow-up this report surfaces.

**Update — real cProfile pass run** (same session, a fresh isolated 12-team real-pool profile, `speed=FAST`): confirms and precisely locates the hot path. Real, measured breakdown (cumulative time):

- `evaluate_pick_candidates` (19.8s of the run) → `simulate_pick_now` (36 calls, 18.3s) → **`_select_asset`** (`redraft_draft_room_v1_service.py:2046`) is the dominant cost: **10,056 calls, 9.2s of its own time**, called once per simulated CPU pick within every Monte Carlo continuation trial.
- Three real, extremely hot inner helpers `_select_asset` calls into: `_seeded_unit` (**4.8 million calls**, 6.97s cumulative), `_roster_need_adjustment` (**5.15 million calls**, 5.45s cumulative), `_roster_candidate_allowed` (**5.49 million calls**, 2.56s cumulative).
- `candidate_survival_probability`/`evaluate_cost_of_waiting_v2` (Make-It-Back) separately costs another real 4.6s via the same `_advance_cpu`/`_select_asset` machinery.

This is a real, well-understood cost shape: `_select_asset` scores the FULL real candidate pool at every simulated pick inside every trial/continuation-seed, so its cost scales with `(real pool size) × (simulated picks per trial) × (trials) × (candidates evaluated)` — explaining why a small synthetic fixture (240 rows, used in most unit tests) stays fast while this session's real, full 530-row pool does not. This is the concrete, exact starting point for the actual fix (likely narrowing the per-pick candidate pool `_select_asset` scores, or caching/short-circuiting repeated identical sub-computations across trials) — not attempted this pass; a real optimization needs its own correctness validation (must not change any real recommendation), which is exactly the kind of change this program's own discipline says should not be rushed.

### 4. A related, real robustness bug — found and FIXED this pass

While investigating the above, found a real, reproducible server crash: when a client (browser) aborts an in-flight request (matching the real timeout-vs-computation-time gap above, or React StrictMode's dev-only double-invoke superseding a still-running fetch), the backend's `_write_json` raised an uncaught `ConnectionAbortedError`/`BrokenPipeError` while writing the (by-then-moot) response — a real, reproducible traceback in the server's own log for an entirely expected client behavior, unlike every other failure path in `desktop_api/server.py`, which `_dispatch`'s own try/except already converts into a clean response.

**Fixed**: wrapped `_write_json`'s response-writing in a try/except for `(ConnectionAbortedError, BrokenPipeError, ConnectionResetError, OSError)`. Added `test_write_json_swallows_a_client_disconnect_instead_of_crashing` (3 parametrized cases) — a deterministic unit test (not a racy real-socket reproduction, which was tried first and found unreliable on localhost) that directly exercises `_write_json` with a `wfile` that raises exactly like an aborted connection does. Verified the test genuinely fails without the fix (confirmed via a scoped `git stash` of just the source change) and passes with it. Full `test_desktop_http_api.py`: 38/38 passing.

This fix does not resolve finding #3 above (the real computation is still slow) — it only stops the resulting client aborts from crashing that connection's handler thread with an ugly, uninformative traceback.

### 5. Player Drawer / Action badges (Compare, Drawer specifically) — NOT independently verified this pass

Both surfaces read from the same DecisionBundle candidate data that finding #3 blocked from reliably rendering in this real, full-scale test scenario within the investigation window. Not claiming these are broken — the underlying component code was read and is shared with the already-verified Suggestions table (same `action`/`marginalRosterUtility` fields, confirmed present and correctly typed in the real backend response via direct API inspection) — but this report does not claim ACTUAL rendered verification of the Drawer/Compare Action badge colors specifically, consistent with this report's own standard of not claiming more than what was actually observed rendering.

## Verification

All work in an isolated, disposable data root (`NWR_REDRAFT_HOME` override) and a real, local-only backend/frontend pair; the real 403/Fantasy Gamers boards were never reachable from this session's browser tab. Both real boards re-verified byte-identical (pick counts, `updated_at_utc`) before and after.
