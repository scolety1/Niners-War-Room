# NWR BIG DRAFT — FINAL RUNBOOK

Written against your REAL local NWR installation (not a sandbox). Keep this open on draft night.

## ⚠️ 0. THE ONE THING YOU NEED TO CONFIRM FIRST

This session checked your two real, non-practice leagues directly:

| League | Real status, checked tonight |
|---|---|
| **2026 KHA High Stakes League** (ESPN, 16-team) | Already fully drafted — 157 real picks recorded, 2026-09-03. Not tomorrow's draft. |
| **Fantasy Gamers** (Sleeper, 10-team PPR) | Checked live against Sleeper's own API just now: status `pre_draft`, no picks made yet, real scheduled start **2026-09-09, ~3 days from now** — not tomorrow either. |

**Neither of your two known real leagues is scheduled for tomorrow night.** If a different real draft is happening tomorrow, it isn't set up in NWR yet under any of your 5 saved profiles — confirm which league it is and, if new, set it up (team count, scoring, roster) before the clock starts. If "tomorrow" was approximate and you meant the Fantasy Gamers draft on the 9th, everything below is already ready for it.

## A. Launch

Same launcher as always (`desktop/launch-draft-upgrade-preview.bat`). Nothing about how you start the app changed.

## B. Which league profile

You have 5 saved profiles. The real ones:
- **Fantasy Gamers** (Sleeper, 10-team PPR) — real, pre-draft, most likely candidate if your Sleeper draft is what's coming up.
- **2026 KHA High Stakes League** — already drafted, don't reuse for a new draft.
- **2026 KHA High Stakes League — PRACTICE** — safe practice copy, use this to rehearse.
The other two ("10-team 1QB Standard", "2026 KHA High Stakes League — TEST") are generic/test, not real leagues.

If tomorrow's league isn't one of these, create a new profile with the real settings before you draft.

## C. Set draft slot

League setup → draft slot picker, as always.

## D/E. Record picks (opponent and yours)

Unchanged — the app's normal pick-capture flow. Confirmed again tonight via a real rehearsal against your actual practice board: recommendations correctly recalculate after every pick.

## F. Undo

Unchanged. Confirmed tonight against your real practice board.

## G. Reset

Starting fresh on the same profile wipes the board — same as before.

## H. Enable V2 shadow (backend only — no visible toggle yet)

A new, historically-validated Team Score V2 / Championship Equity V2 layer now exists as a real, separate backend endpoint (`POST /api/v1/redraft/draft/{profile}/decision-bundle-v2`), tested tonight against your real KHA practice board with real results (agreed with the existing V1 pick every time in a 3-round rehearsal). **There is no visible toggle for it in the app yet** — wiring a UI switch was intentionally not attempted tonight (the frontend component is large and this session can't build/render the app to verify a change to it safely). Nothing changes in what you see tomorrow; V1 (Player Score, Pick Score, Team Score, Championship Equity, Cost of Waiting, Make-It-Back) is exactly what you already know and is unaffected.

## I. What numbers matter

Same as always: **Pick Score → Player → Team Score after/delta → Make-It-Back/Cost of Waiting → Championship Equity after/delta → Player Score → reason → evidence status.**

## J. What DATA_LIMITED means

A real, visible, draftable player with no NWR score because its projection data is too stale to trust. Confirmed real tonight: 78 rookies are in exactly this state (last governed refresh 2026-07-30), unchanged since your last draft. Use market ADP only for these players.

## K. Real governance action taken tonight

Your practice-draft data approval had expired (`valid_until: 2026-09-05`). Using your own explicit authorization and the real, existing governance mechanism (no bypass, same unchanged 530-player/78-blocked-rookie snapshot, independently re-verified byte-identical), **this session renewed it through 2026-09-09** — covering tonight's rehearsal and the confirmed Fantasy Gamers draft date. Your real, separate KHA draft-day approval (already expired 2026-09-03) was not touched or extended — it doesn't need to be; that draft is done.

## L. Final pre-draft refresh (if you get a fresher data pull before draft time)

```
python -c "
from src.services.redraft_engine_v1_service import install_projection_snapshot
install_projection_snapshot(
    root=r'C:\Users\<you>\AppData\Local\com.ninerswarroom.redraft\state\redraft',
    season=2026,
    source='<path to the freshly re-exported, already-governed 2026 projection CSV>',
    approval_receipt='<path to a valid, non-expired approval receipt JSON>',
)
"
```
This is the exact real mechanism this session used tonight to renew the approval — it swaps which already-governed CSV is read, never retrains anything. Generate one recommendation afterward as a smoke test.

## M. Emergency fallback

Unchanged from the app's existing design: if Championship Equity or Cost of Waiting ever errors, Player Score / Pick Score keep showing. A `DEGRADED` V2 status (if you ever call the new endpoint directly) never affects the V1 fields you actually see.

## N. Where logs live (on your real machine)

- Operational diagnostics: `...\state\redraft\owner_test_instrumentation\<profile_id>\events.jsonl`
- **New tonight, and already proven working against your real practice board**: `...\state\redraft\prospective_decision_log\<profile_id>\decisions.jsonl` — every recommendation and every pick, cross-referenced, starting real 2026 evidence collection. Never used to retrain anything mid-season.

## What was verified tonight, for real, against your actual data

- Real V1 DecisionBundle: real players (Jonathan Taylor topped the real practice board's recommendation), FAST latency ~1.9–2.5s.
- Real V2 challenger: same top pick as V1, correctly labeled `TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED` for your real 16-team league (no real league matches the thin shape the historical validation used), FAST latency ~1.8–2.1s.
- A real 3-round mock through your real practice board: recommend → pick → recalculate, zero V1/V2 disagreements, real undo, prospective log wrote 6 real rows — then the practice board was restored to its exact original state (backed up first, verified byte-for-byte after).
- Full regression: 3865 passed / 324 failed / 71 skipped — the 324 is your established baseline, unchanged. Zero regressions from anything tonight.

See `NWR_BIG_DRAFT_READINESS_OVERNIGHT_V1_REPORT_20260906.md` and its real-install addendum for the complete evidence trail.
