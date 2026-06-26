# NWR Live Draft V2 Interactive Smoke - 2026-06-26

## Verdict

GREEN for merge-review readiness with one remaining UI automation caveat: the browser tool used for this smoke exposes the file chooser but does not expose a supported file-upload method, so import-file selection was verified by service tests and UI control presence rather than a full automated browser file upload.

## Environment

- Branch: `work/live-draft-v2-reliability-20260626`
- Worktree: `C:\NWR\Niners-War-Room-live-draft-v2-reliability-20260626`
- Port: `8600`
- Runtime root: `C:\NWR_SHARED_DATA\draft_runtime_state_ui_smoke_20260626_formfix`
- Runtime root status: isolated local smoke state, not tracked

## Pages Tested

- `/live-draft-room`
- `/post-draft-mode`
- HTTP route sweep also returned 200 for:
  - `/drafting-mode`
  - `/cheat-sheets`
  - `/trading-lab`
  - `/rankings`
  - `/mock-draft`

## A. Live Draft Room Persistence

Actions:

1. Opened `/live-draft-room`.
2. Used the visible default player/pick controls.
3. Clicked `Assign Pick`.
4. Confirmed the UI moved from `Drafted: 0` to `Drafted: 1`.
5. Confirmed current pick advanced to `1.02`.
6. Reloaded the page.
7. Confirmed `Drafted: 1` and current pick `1.02` persisted.

Result: PASS.

## B. Trade Event Workflow

Required trade:

- Give: `1.04`
- Receive: `2028 1st + 2.03`

Initial finding:

- The first automated smoke found a UI-readiness issue: text fields appeared filled in the browser, but the non-form Streamlit button submitted blank/default values to runtime state.
- Fix applied: the Record Trade controls are now wrapped in a Streamlit form so values submit atomically with `Record trade`.

Retest actions:

1. Opened `Record Trade`.
2. Entered:
   - Team B: `WhoDat`
   - Team A sends: `1.04`
   - Team B sends: `2028 1st + 2.03`
   - Notes: `UI smoke verified trade`
3. Verified DOM values before submit.
4. Clicked `Record trade`.
5. Confirmed no traceback.
6. Inspected persisted runtime state.

Persisted state proof:

- `TRADE_COUNT=1`
- `TEAM_B=WhoDat`
- `TEAM_A_SENDS=1.04`
- `TEAM_B_SENDS=2028 1st + 2.03`
- `FUTURE_PICKS=2028 1st`
- `OVERRIDE_104=WhoDat`
- `OVERRIDE_203=NWR`
- `LAST_EVENT=trade_recorded`

Reload proof:

- Reloaded `/live-draft-room`.
- Confirmed `Drafted: 1`, `WhoDat`, runtime controls, and no traceback.

Result: PASS after form fix.

## C. Export / Import Workflow

Actions:

1. Opened `Runtime draft state / export / reset`.
2. Confirmed import controls are visible:
   - `Import JSON`
   - `Confirm restore imported JSON`
3. Clicked `Export JSON`.
4. Confirmed UI success text and no traceback.
5. Confirmed export files were written:
   - `draft_day_v2__live_draft_log.json`
   - `draft_day_v2__live_draft_log.csv`
   - `draft_day_v2__live_draft_log.md`

Import preview / confirmation:

- UI controls are visible.
- Service tests cover:
  - import preview summary
  - overwrite blocked without confirmation
  - successful import only after confirmation
  - backup before import
- Full automated browser upload was not completed because the available browser API does not expose a supported file-upload method for the Streamlit file picker.

Result: PASS for export and import-control readiness; YELLOW-GREEN for automated file-upload proof.

## D. Post-Draft Mode

Actions:

1. Opened `/post-draft-mode`.
2. Confirmed no traceback.
3. Confirmed page shows:
   - `Drafted: 1`
   - `Trades: 1`
   - `Events: 3`
4. Confirmed page labels runtime state as audit/display data, not official source truth.

Result: PASS.

## Guardrails

- No model trade valuation added.
- No DynastyProcess, ADP, or market values used for trade value.
- No rank, tier, Dynasty Rank, Final Board Rank, frozen board, pinned snapshot, latest candidate, or latest approved mutation.
- No CFBD/NFL usage gate changes.
- No decision-page evidence wiring.
- No hosted deployment.

## Merge Review Status

Safe for merge review. Recommended merge-review note: import file upload still deserves one final human/browser click-through because automation could not select a local JSON file through the Streamlit file picker, even though service tests and UI controls pass.
