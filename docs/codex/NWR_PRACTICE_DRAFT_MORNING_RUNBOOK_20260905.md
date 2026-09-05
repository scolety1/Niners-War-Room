# NWR Practice Draft — Morning Runbook

**Read this first. It's short.**

## ✅ Already handled: the approval blocker

Last night's readiness pass found live pick-recording blocked (the 2026 projection data's governance approval was scoped only to the real 2026-09-02 KHA draft and had expired). **You explicitly authorized a new, practice-draft-scoped approval, and it's already installed and verified working** — see `docs/codex/NWR_PRACTICE_DRAFT_APPROVAL_AND_LIVE_SMOKE_TEST_20260905.md` for the full record. Nothing further needed here; a full live smoke test on the real installation passed all 15 steps, and the real KHA draft board was confirmed untouched throughout.

**A ready-to-use practice profile is already waiting for you**: "2026 KHA High Stakes League — PRACTICE 20260905" (16 teams, full PPR, matches KHA's real format exactly). Just select it and click start — it has a few leftover picks from last night's testing, so hit "start new draft room" once before your real session to get a clean board.

## 1. What do I launch?

Double-click `desktop\launch-draft-upgrade-preview.bat`. It's a dev-mode build sharing your real data — a fresh fix landed in the last commit before tonight, and it was not touched further tonight.

## 2. What league/config do I select?

- **"2026 KHA High Stakes League — PRACTICE 20260905"** — use this one. Created and verified tonight.
- **"2026 KHA High Stakes League"** — your real draft, completed 2026-09-02. **Do not use this for practice** — it has a full 192-pick board already.
- **"2026 KHA High Stakes League — TEST"** — has some read-only Sleeper-tracking picks from Sept 2-3 on it already; the PRACTICE profile above was duplicated from this one so you don't need to touch it.

## 3. Where do I enter/select my draft slot?

Set it when you start the draft room (owner slot + seed + speed). If unsure, any slot works — the recommendation engine adapts to whichever slot you pick.

## 4. How do I record picks?

Draft Room's rapid-capture entry (the main `/` route) — fast keyboard pick entry, built for speed. Draft Room V2 (`/draft-room-v2`) is the decision-support view (Suggestions/Team/Compare) layered on the same live state — it doesn't take picks itself.

## 5. How do I undo?

"Undo" button in the Draft Room — reverses exactly one pick. Verified tonight (mechanically, via a full synthetic rehearsal): works correctly.

## 6. How do I reset?

Starting a new draft room on the same profile *is* the reset — it wipes to an empty board. To keep a prior board around, duplicate the profile first instead of resetting in place.

## 7. What numbers should I pay attention to?

- **Player Score** — the core, production, unchanged value ranking.
- **Cost of Waiting / Make-It-Back %** — how much you lose by not taking this player now, and the odds they're gone by your next pick. Externally validated (~0.57 Brier Skill Score vs. base rate).
- **Team Score (current / Team Score if drafted / delta)** — how a pick changes your projected roster strength. Its underlying methodology was externally validated across 11 real historical seasons (2012-2024) this week — genuinely more evidence behind it than before.

## 8. What is experimental / should not be trusted yet?

- **Championship Equity numbers** — labeled "SIMULATED RESEARCH" in the UI; treat as directional, not precise.
- **Pick Score** — labeled experimental; it's a real, disclosed combination of the above, not an independently-validated single number.
- **Historical Replay tab** — a static, disclosed proxy preview from 2026-09-02, unrelated to your live draft. Don't read it as real-time evidence.

## 9. Where is the practice-draft log saved?

`owner_test_instrumentation/<profile_id>/events.jsonl` under your NWR data folder (`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\`). Records latency, top candidates, and every draft-state change automatically — no action needed.

---

## 5-minute pre-draft checklist

1. Launch via `desktop\launch-draft-upgrade-preview.bat`.
2. Select **"2026 KHA High Stakes League — PRACTICE 20260905"**.
3. Start a new draft room to clear last night's test picks, with your real slot/seed.
4. Make one test pick and undo it, just to confirm the loop is live before the real clock starts.
5. If you want 2026 rookies included: 78 real rookies are currently excluded (their own data is independently stale) — this wasn't part of last night's approval and needs a separate decision if it matters for your practice session.
