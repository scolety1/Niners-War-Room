# NWR BIG DRAFT — MORNING RUNBOOK

> **SUPERSEDED (2026-09-06, later the same day)** by `NWR_BIG_DRAFT_FINAL_RUNBOOK_20260907.md`, written after this session gained real access to your actual local NWR installation (not just the isolated sandbox this file was written against). Use the FINAL runbook — it has real findings this one couldn't see, including a real schedule question you need to answer before tomorrow. This file is preserved unedited below as the historical record of the sandboxed-only pass.

Keep this open on draft night. Everything else from tonight is background reading; this is the short version.

## A. Launch

Use the same Draft Upgrade Preview launcher you already use (`desktop/launch-draft-upgrade-preview.bat`). Nothing about how you start the app changed tonight.

## B. League profile to use

**Tonight's session could not confirm your exact real league for tomorrow** (this sandboxed environment has no access to your saved profiles). Before you draft, in the app, confirm/select:
1. **Team count** — 8, 10, or 12 (16 also works if it's another KHA-sized league).
2. **QB format** — 1QB or Superflex/2QB.
3. **PPR format** — Standard / Half-PPR / Full PPR.
4. **K/DST on or off**, bench size.
5. **Your draft slot.**

Everything built tonight was tested and confirmed working at all of 8/10/12/16-team; none of it depends on which one you pick.

## C. Set draft slot

Draft Room → league setup → draft slot picker, as usual.

## D. Record an opponent pick

Draft Room's normal pick-capture flow, unchanged.

## E. Record your own pick

Same as always. Recommendations recalculate automatically after every pick — confirmed again tonight via a real rehearsal (not just claimed).

## F. Undo

Same undo button as always — confirmed tonight to correctly restore the exact prior state (roster, available pool, recommendations) at every league size tested.

## G. Reset

Starting a fresh draft on the same profile wipes the board clean — this is the real "reset," not a separate button. Confirmed tonight.

## H. What numbers matter

Trust, in this order: **Player Score → Pick Score → Team Score → Cost of Waiting / Make-It-Back → Championship Equity.** These are exactly the same fields you already know — nothing about what's visible in the app changed tonight. (A new, more rigorously-validated Team Score V2 / Championship Equity V2 layer was built and tested tonight but is NOT wired into the visible UI yet — it exists as a separate, opt-in layer for a future session to enable deliberately.)

## I. What DATA_LIMITED means

A player (mostly rookies with stale or no governed projection) is real, visible, and draftable — but NWR has not assigned it a Player Score / Team Score / Cost-of-Waiting number, because doing so would mean guessing. Use market ADP as your only guide for these players; don't expect an NWR opinion on them.

## J. Final pre-draft refresh (run 60-90 min before the draft, if you have a fresher data pull)

```
python -c "
from src.services.redraft_engine_v1_service import install_projection_snapshot
install_projection_snapshot(
    root='<your real NWR data root>',
    season=2026,
    source='<path to the freshly re-exported, already-governed 2026 projection CSV>',
    approval_receipt='<path to a valid, non-expired approval receipt JSON>',
)
"
```
This swaps which already-governed CSV the app reads — it does **not** retrain or retune anything. After running it, generate one recommendation as a smoke test before trusting it live.

**Known blocker found tonight**: the practice-draft approval receipt on record (`docs/codex/NWR_PRACTICE_DRAFT_APPROVAL_AND_LIVE_SMOKE_TEST_20260905.md`) was issued with `valid_until: 2026-09-05` — that's yesterday relative to tonight. If a practice run says "Projection approval receipt has expired," you need a fresh receipt (same shape as before, same `source_sha256`, new `valid_until`) — this was **not** renewed automatically tonight; it needs your real, explicit approval, not something to fabricate.

## K. Where real draft logs go

- Operational diagnostics (latency, errors): `owner_test_instrumentation/<profile_id>/events.jsonl` under your app's data directory, as before.
- **New tonight**: a full point-in-time decision log — every recommendation and every pick you actually made, cross-referenced — at `prospective_decision_log/<profile_id>/decisions.jsonl` under the same data directory. This starts building real 2026 evidence from your very first pick. It is never used to retrain anything mid-season.

## L. Emergency fallback if an advanced metric fails

Nothing changed about the live app's own error handling tonight. If Championship Equity or Cost of Waiting ever errors out, the app has always been built to keep showing Player Score / Pick Score rather than blocking you — that behavior is unchanged. If you see a `DEGRADED` or `UNAVAILABLE` status on any field, keep drafting using the numbers that ARE showing; nothing about a degraded secondary metric should stop you from picking.

---
See `NWR_BIG_DRAFT_READINESS_OVERNIGHT_V1_REPORT_20260906.md` for the full evidence behind every claim above.
