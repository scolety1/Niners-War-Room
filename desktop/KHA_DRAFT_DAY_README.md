# 2026 KHA High Stakes League — Draft Day (2026-09-02)

## Exact launcher

Double-click **`LAUNCH_KHA_HIGH_STAKES_DRAFT.bat`** in this folder (or the desktop shortcut
**`NWR — KHA HIGH STAKES DRAFT`**). It runs the Redraft desktop app in Tauri dev mode against the
real Python service in this exact worktree, with `NWR_DESKTOP_PYTHON` pointed at a real interpreter
(the Windows `python.exe` App Execution Alias was not reliably found by the app's own PATH scan —
this was found and fixed tonight; see the readiness report). Verified tonight: a real window titled
**"Niners War Room — Redraft"** opens, and its Python backend child process starts and binds a real
loopback port.

## Which profile to use

Open the profile switcher and select **`2026 KHA High Stakes League`** (NOT the `— TEST` one) for the
real draft tomorrow. It shows 16 teams, ESPN, full PPR, 12 rounds, and 0 picks.

Use **`2026 KHA High Stakes League — TEST`** for any more rehearsal tonight — it is fully isolated
from the real profile's draft state.

## How to select your draft slot

ESPN reveals the randomized draft order about an hour before the draft. In the Draft Room's
"Set your draft slot" panel, pick your slot (1–16) from the dropdown, then Start Draft. This does not
require recreating the league — the same profile supports any slot.

## How to refresh/paste ESPN ADP

Go to **Paste Rankings / ADP**, paste your platform's rankings table (a markdown-style table with
Position / Player / Consensus / Sleeper / ESPN / FantasyPros columns), select **ESPN** as the source,
review the match preview, then Save & Activate. The league's `provider` is already set to `espn`, so
the Draft Room auto-detects ESPN as the platform. Do this again right before the real draft starts
with the freshest table you have — re-pasting is the normal way to keep it current, and the app now
correctly ages a pasted snapshot's freshness label (FRESH → RECENT → STALE) instead of showing FRESH
forever.

## How to checkpoint

Run **`SAVE_KHA_DRAFT_CHECKPOINT.bat`** any time (before the draft, and again mid-draft if you want a
safety copy). It copies the REAL profile's configuration, draft board, manual K/DST assets, ADP/
provider state, and projection files into a new timestamped folder under
`local_exports\redraft_v1_checkpoints\`. It only ever adds a new folder — it never deletes or
overwrites anything.

## Emergency recovery

If something looks wrong mid-draft:

1. Close the app.
2. Look in `local_exports\redraft_v1_checkpoints\<latest timestamp>\` for your most recent checkpoint.
3. Copy the files back into `local_exports\redraft_v1\` (matching the same relative paths) to restore
   that state, then reopen the app.
4. The in-app **Undo** button reverses the single most recent pick without needing a checkpoint at all.

## Remaining caveats (read before you draft)

- **Projection data governance**: The bundled 608-player projection's owner-approval had expired
  (2026-08-29). Tonight, under the explicit draft-day authorization given in this session, a narrowly
  scoped, time-limited (expires 2026-09-03) local renewal was issued — the projection artifact itself
  is byte-for-byte unchanged (verified by SHA-256). This does not touch canonical/HQ data.
- **Rookie coverage**: All 78 2026 rookie rows were previously invisible on the board because their
  data is older than the app's normal 30-day freshness gate. Under the same draft-day authorization,
  they are now shown with an explicit **"NWR ROOKIE PRIOR — DRAFT-DAY OWNER APPROVED"** label — their
  projection values and dates are unchanged, only the freshness gate was bypassed for this draft.
- **Kicker rosters**: 27 of 32 manual kicker entries were corrected/confirmed tonight via a live web
  check; 5 (BAL, IND, LV, NO, NYJ) are flagged **unsettled** due to active competitions or conflicting
  reports as of 2026-09-01 — see `KHA_DRAFT_ALERTS_2026-09-02.md`.
- **Current injury/status context**: `KHA_DRAFT_ALERTS_2026-09-02.csv` / `.md` in this folder list a
  bounded set of season-ending and Week-5-return injuries found tonight (not an exhaustive top-250
  scan). Treat it as a prompt to double-check, not a final answer.
- **No IR roster slot** exists in this engine's data model — not needed for the draft itself (only 12
  active rounds are drafted), only relevant to later in-season roster management, which is out of
  scope tonight.
- **2-point conversion scoring** is not modeled (no such field exists in the engine) — negligible
  fantasy-point impact.
- No packaged installer (.exe/.msi) was produced — this dev-mode launch is tonight's verified path.
