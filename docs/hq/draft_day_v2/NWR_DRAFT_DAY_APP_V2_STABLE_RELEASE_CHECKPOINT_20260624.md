# NWR Draft-Day App V2 Stable Release Checkpoint

Date: 2026-06-24
Branch: `work/hq-parallel-control`
Stable HEAD: `539463a41f063b9c9995c198e138c1d8676fca3e`

## Verdict

Draft-Day App V2 is checkpointed as the stable local Master state after:

- Drafting Mode Cockpit V1.
- Live/Mock Draft session separation.
- Refresh Data integration.
- Settings/Data Health preservation.

This is a recovery and release checkpoint. It does not approve model, rank, tier, source-truth, frozen-board, latest-file, or pinned-snapshot changes.

## Verified State

- Branch: `work/hq-parallel-control`.
- Sync: clean and even with `origin/work/hq-parallel-control`.
- Starting and rollback HEAD: `539463a41f063b9c9995c198e138c1d8676fca3e`.
- Frozen board row count: `66`.
- Frozen board source path observed by the app: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`.
- Pinned manifest hash: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- Expected pinned manifest hash: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- Pinned hash status: unchanged.
- `latest_candidate` and `latest_approved`: untouched by this checkpoint.
- Runtime/shared/export/raw files: not added by this checkpoint.

## Current GREEN Feature Set

- Drafting Mode Cockpit: `/drafting-mode` opens as the on-clock cockpit, not a navigation hub.
- Live/Mock Draft session selector: cockpit top bar exposes `Live Draft` and `Mock Draft / Practice`.
- Separate live/mock runtime state: live and mock state are stored independently by the runtime service.
- Persistent draft state: save, load latest, export, reset, mark drafted, and notes respect the selected session type.
- Trade event recorder: cockpit and Live Draft V2 trade events persist locally and update parseable pick ownership overrides.
- Refresh Data: central refresh page/control remains before Mock Draft in navigation and in the cockpit top bar.
- Settings/Data Health dashboard: includes Refresh Data Run Status and source/data health checks.
- Dynasty Rankings full board: 240-row dynasty board remains available through `/rankings` and `/home`.
- DynastyProcess display-only market context in Rankings: visible as context only, not model truth.
- Trading Lab market sanity: DynastyProcess market sanity remains display-only.
- Player Compare Decision Mode: compare summary and caveats remain available.
- Post-Draft Mode: defaults to live state and reads persisted runtime events.
- Cheat Sheet tiered board polish: tiered board, K/DST hidden by default, and runtime drafted filtering remain available.
- Frozen board demotion: Frozen Final Draft Board V1 remains a baseline/checkpoint, not full source truth.
- Model evaluation harness: audit/evaluation support remains present.
- Model warning repair: warning repair from the prior stable lane remains preserved.

## Refresh Data Checkpoint

Refresh Data remains integrated and preserved:

- Route: `/refresh-data`.
- Navigation placement: immediately before `Mock Draft`.
- Cockpit top bar: links to `/refresh-data`.
- Status path read by Data Health: `local_exports/refresh_data/latest_refresh_status.json`.
- DynastyProcess market baseline: safe configured refresh.
- Sleeper league data: safe configured refresh.
- nflverse: skipped unless the slow runner is explicitly opted in.
- CollegeFootballData: not configured.
- RotoWire/vendor exports: blocked/manual.
- Gmail/email bodies: not pulled.

Refresh Data does not mutate ranks, tiers, frozen board files, latest pointers, pinned snapshots, runtime draft picks, or model/source-truth logic.

## Runtime State

Runtime state is local-only and ignored/untracked.

- Runtime root: `C:\NWR_SHARED_DATA\draft_runtime_state`.
- Live state file shape: `state\draft_day_v2__live.json`.
- Mock state file shape: `state\draft_day_v2__mock.json`.
- Export root shape: `exports\`.
- Backup root shape: `backups\`.

Mock state is practice-only. It must not affect live draft state. Post-Draft Mode defaults to live state.

## Known Caveats

- Full Dynasty source has 0 rookie/prospect rows.
- KC Concepcion age remains `Not enough information`.
- Brian Thomas age remains `Not enough information`.
- Actual 2026 draft log has not been imported.
- Actual trade history file has not been imported.
- Gmail/pre-Sleeper evidence intake is metadata/query only, not parsed truth.
- 2010-2021 drop lists are proxy-only and sensitivity-only.
- 2022-2024 drop rows are inferred/unprotected unless upgraded.
- Market, ADP, and DynastyProcess are display-only unless separately approved.

## Start Instructions

From repo root:

`C:\NWR\Niners-War-Room`

Preferred launcher:

```powershell
.\START_DRAFT_DAY_APP.bat
```

PowerShell launcher with explicit port:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_draft_day_app.ps1 -Port 8501
```

Direct Streamlit fallback:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py --server.port 8501 --server.headless true
```

Open Drafting Mode:

`http://127.0.0.1:8501/drafting-mode`

## Restore And Recovery

Recovery point:

`539463a41f063b9c9995c198e138c1d8676fca3e`

Inspect current state:

```powershell
git status --short --branch
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/work/hq-parallel-control
```

Recover the branch to the stable checkpoint only if explicitly approved:

```powershell
git fetch origin
git switch work/hq-parallel-control
git reset --hard 539463a41f063b9c9995c198e138c1d8676fca3e
```

## Clean-State Checks

Verify no runtime/shared files are tracked:

```powershell
git ls-files | Select-String -Pattern '(^|/)(local_exports|runtime|state|exports)/|NWR_SHARED_DATA|draft_runtime_state'
```

Verify no latest/pinned/source-truth files are part of the current diff:

```powershell
git diff --name-only HEAD | Select-String -Pattern 'latest_candidate|latest_approved|pinned|final_board|frozen|local_exports|NWR_SHARED_DATA|runtime|vendor|gmail|email'
```

Verify formatting:

```powershell
git diff --check
```

## Browser Smoke

Result: passed on `http://localhost:8612`.

Smoke routes for this checkpoint:

- `/drafting-mode`
- `/refresh-data`
- `/settings-data-health`
- `/rankings`
- `/player-compare`
- `/trading-lab`
- `/mock-draft`
- `/post-draft-mode`
- `/cheat-sheets`
- `/live-draft-room`

Observed result:

- Each route opened without traceback markers.
- `/drafting-mode` showed Drafting Mode, `Draft Session:`, and Best Available Board.
- `/refresh-data` showed Refresh Data.
- `/settings-data-health` showed Settings, Data Health, and Refresh Data Run Status.
- `/rankings` showed Dynasty Rankings.
- `/player-compare` showed Player Compare.
- `/trading-lab` showed Trading Lab.
- `/mock-draft` showed Mock Draft.
- `/post-draft-mode` showed Post-Draft Mode.
- `/cheat-sheets` showed Cheat Sheets.
- `/live-draft-room` showed Live Draft Room.

## Guardrails

This checkpoint does not:

- mutate Frozen Final Draft Board V1.
- change `final_board_rank`.
- overwrite Dynasty Rank.
- change tier assignments.
- update `latest_candidate` or `latest_approved`.
- mutate pinned snapshots.
- change model/rank logic.
- make DynastyProcess, ADP, market, vendor, or projection fields model inputs.
- track runtime JSON.
- track `C:\NWR_SHARED_DATA`.
- track `local_exports`.
- add raw vendor files or email bodies.
