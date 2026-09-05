# NWR Practice Draft — Morning Runbook

**Read this first. It's short.**

## ⚠️ Before you launch: one required action

**NWR's live pick-recording is currently blocked for every league, including KHA — this must be fixed before you draft anything.**

Why: the 2026 player-projection data's governance approval is real, and was deliberately scoped to *only* the actual 2026-09-02 KHA draft ("`Use limited through completion of the 2026-09-02 draft`... `Does not authorize future/in-season use beyond this draft`"). It expired 2026-09-03. This isn't a bug — it's the system correctly refusing to use data outside its approved scope — but it means every pick-marking/recommendation call will fail right now with "The active Redraft ranking is unavailable" until a new approval covering practice-draft use is issued.

**What to do**: issue a new, brief governance approval (same already-approved, unchanged player data — nothing about the actual projections needs re-review, just the scope/date). This is a real decision only you can make; nothing was fabricated on your behalf overnight. See `docs/codex/NWR_PRACTICE_DRAFT_READINESS_OVERNIGHT_V1_REPORT_20260905.md` section "Critical Finding" for the exact file to update.

Everything below assumes that's done.

## 1. What do I launch?

Double-click `desktop\launch-draft-upgrade-preview.bat`. It's a dev-mode build sharing your real data — a fresh fix landed in the last commit before tonight, and it was not touched further tonight.

## 2. What league/config do I select?

You have two real KHA-shaped profiles already saved:
- **"2026 KHA High Stakes League"** — your real draft, completed 2026-09-02. **Do not use this for practice** — it has a full 192-pick board already.
- **"2026 KHA High Stakes League — TEST"** — has some read-only Sleeper-tracking picks from Sept 2-3 on it already. If you want a truly clean practice board, duplicate it first (Profile page → Duplicate) rather than drafting on top of that history.

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

1. **Renew the governance approval** (see the warning at the top — nothing else works until this is done).
2. Launch via `desktop\launch-draft-upgrade-preview.bat`.
3. Select or duplicate the correct profile (never the real completed KHA board).
4. Start the draft room with your real slot/seed.
5. Make one test pick and undo it, just to confirm the loop is live before the real clock starts.
