# NWR DECISION ENGINE V1 — OWNER REVIEW PACKAGE

**For Spencer Colety's review. This package explains what has been validated, exactly how it would enter the live Draft Room if adopted, and what it does NOT change today. No production promotion has occurred.**

## 1. What "historically validated" means here

`NWR_DECISION_ENGINE_V1_HISTORICALLY_VALIDATED` = the frozen candidate commit `d55bab2c14591172f662a09c627d90af551fa38a`, evaluated against 9 development seasons, two prior sealed holdouts (2016, 2024), and now the final 2025 sealed holdout — verdict `GREEN_2025_FINAL_HOLDOUT_PASSED`. See `NWR_FINAL_2025_HOLDOUT_EVALUATION_V1_RESULT_20260906.md` for the numbers, and `NWR_HISTORICAL_TUNING_PROGRAM_V1_CLOSEOUT_REPORT_20260906.md` for the full program summary.

## 2. What is real and strong vs. real but weaker

| Component | Verdict | Owner-facing meaning |
|---|---|---|
| Player Score | Strong | Beats the market (ADP) at ranking who scores well, overall and at every position |
| Team Score V2 | **Strong — the primary number** | Reliably tells you whether one roster is better than another |
| Draft strategy (position-cap fix) | Strong | The drafting logic no longer hoards one position past a sane limit; beats ADP and a random-legal floor in simulation |
| Pick Score (clear decisions) | Strong | When one pick is obviously better than another, the tool says so correctly |
| Championship Equity | Real, but modest | Directionally right, but not yet a confident predictor of championship odds on its own |
| Pick Score (close calls) | Weak, by design | When two picks are genuinely close, the tool's numeric edge between them is not reliable — this is flagged, not hidden |
| Decision Confidence | **Not validated — do not trust its confidence label** | The tool cannot yet tell you when it's more or less sure of itself; treat every recommendation as equally uncertain until this changes |

## 3. Exactly how this would enter the live Draft Room, if you choose to adopt it

Nothing has been switched on. If and when you decide to move forward, the intended path (not yet executed) is:

1. **Shadow-only rollout first** — the frozen candidate's outputs (Player Score, Team Score V2, Pick Score) run alongside the current live board, visible in a clearly-labeled shadow panel, never replacing or reordering what the live board already shows. This program's existing shadow-replay infrastructure (`kha_shadow_replay_reader_service.py`, the "Historical Replay" tab already shipped in Draft Room V2) is the real, already-built pattern this would extend — read-only, explicitly labeled, never silently upgraded to look "current."
2. **Practice-draft validation next** — before any live-draft use, the frozen candidate is exercised inside the isolated practice-draft environment (pick recording, after-pick score updates, undo/reset, league-size variants) with zero write access to the real KHA board. See Section 5 below for what remains to be built/run here — this has not yet been executed as part of tonight's work.
3. **Owner go/no-go** — only after shadow + practice-draft evidence accumulates does a production-promotion decision belong to you. This report does not recommend a timeline for that decision.

## 4. League-size support

| League size | Status |
|---|---|
| 12-team | Historically validated (this is the size every development season, both prior holdouts, and the 2025 holdout used) |
| 8/10/16-team | `TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED` — the underlying services accept these configurations and will run without error, but no historical evidence exists at these sizes specifically; treat their output as reasonable-but-unproven until a dedicated evaluation is run |

## 5. Honest gaps before any live adoption

- **No live functional shadow-mode integration test was executed tonight.** The real infrastructure this would build on exists (Section 3), but exercising the frozen candidate's newest piece (`ROSTER_CAPPED_GREEDY_NWR`) through the actual practice-draft UI/API path, end-to-end, has not been done as part of this program. See `NWR_DECISION_ENGINE_V1_SHADOW_INTEGRATION_REPORT_20260906.md` for the specific readiness assessment and what remains.
- **Decision Confidence should not be surfaced to you as a trust signal** until it clears a genuine validation (the 2026 prospective protocol is the next real opportunity).
- **Close-call recommendations should be visually distinguished** from clear-cut ones if this is ever surfaced in the live UI — presenting both with the same visual confidence would misrepresent what this program actually found.

## 6. What this package is not

This is not a promotion request, a deployment plan with a date, or a claim that the live Draft Room has changed in any way tonight. It is the evidence and the honest map of what remains, for you to decide what (if anything) happens next.

## 7. BIG DRAFT UPDATE (2026-09-06, same day) — for the real draft tomorrow night

Sections 1-6 above described the *historical* validation. Since they were written, the historically-validated engine has been wired into a real, additive CHALLENGER layer on top of the actual live Draft Room code — this section describes exactly what changed, using real evidence, not a plan.

### 7.1 What is now real and working

- `src/services/decision_bundle_service_v2.py` / `decision_bundle_live_service_v2.py`: a new, opt-in layer that runs Team Score V2 and Championship Equity V2 alongside the existing, unmodified live DecisionBundle (Player Score / Pick Score / Cost of Waiting / Make-It-Back all unchanged). Nothing in the live app calls this yet — it exists and is tested, not switched on.
- Exercised end-to-end through the **real, unmodified** Draft Room code (`start_draft_room`, `owner_pick_and_advance`, `advance_cpu_to_owner`, `undo_room_pick`) for every supported league size (8/10/12/16-team): fresh start, per-pick recommendation, pick recording, candidate-disappears/roster-update checks, undo, resume, reset — all clean, zero errors (`docs/codex/NWR_LIVE_SHADOW_V2_REHEARSAL_OUTPUT_20260906.txt`).
- **Real latency measured** at the actual production FAST/STANDARD/DEEP presets, 12-team: **FAST 0.27s, STANDARD 1.66s, DEEP 4.6s**. All comfortably inside a real draft clock.
- **Prospective decision logging** (`prospective_decision_log_v1_service.py`) is wired and proven: every recommendation and every owner pick is captured as an immutable, append-only record (what NWR knew, what it recommended, what you actually did) — this starts building real 2026 evidence from the very first pick you make, without training on it mid-season.
- The V2 engine is registered as a real Champion/Challenger candidate (`docs/hq/adoption/champion_challenger_registry/decision-bundle-v2-team-score-championship-equity-v1/`) — pending your review, not auto-promoted.

### 7.2 Honest gap: this was NOT tested against your real 2026 data

This session has **no access to your real local NWR installation** (no `local_exports/` data present in this sandboxed environment) — every rehearsal above used clearly-labeled **synthetic** fixture players, never your real governed 2026 board. This means:
- The exact league you're drafting in tomorrow could not be confirmed from anything durable in this repo. **Before you draft, confirm/select: team count (8/10/12/16), QB/Superflex, PPR format, K/DST on or off, bench size, draft slot.** Everything above works correctly for all four supported team counts; it has not been run against your specific real roster shape.
- Your real league's roster shape will **not** match the thin shape Team Score V2/Equity V2 were historically validated against (no real league runs 1 bench spot, no K/DST) — expect every real Team Score V2/Equity V2 field tomorrow to read `TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED`, honestly, not `HISTORICALLY_VALIDATED`. This does not mean it's wrong — it means it hasn't been proven at your exact shape yet.
- The practice-draft data approval on your machine (`valid_until: 2026-09-05`) is a day past its stated expiry as of tonight — you may need to re-approve it before a practice run works. See the Morning Runbook for the exact, minimal fix (this session did not renew it itself — that requires your real authorization, not something to fabricate).
- Team Score V2 numbers compress toward 0 very early in a draft (a roster of 0-1 players scores near the floor of a population built from full rosters) — this is expected model behavior, not a bug; it becomes meaningful after your first few picks.

### 7.3 What this means for tomorrow

Use Player Score / Pick Score / Cost of Waiting / Make-It-Back exactly as before — nothing about them changed tonight. Team Score V2 / Championship Equity V2 exist as a secondary, clearly-labeled, not-yet-wired-into-the-visible-UI signal for you or a future session to enable deliberately. See `NWR_BIG_DRAFT_READINESS_OVERNIGHT_V1_REPORT_20260906.md` for the full verdict and `NWR_BIG_DRAFT_MORNING_RUNBOOK_20260906.md` for the short version.
