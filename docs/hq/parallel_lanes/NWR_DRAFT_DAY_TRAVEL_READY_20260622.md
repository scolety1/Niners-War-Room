# NWR Draft-Day Travel Ready - 20260622

## Verdict

GREEN for travel readiness. The Draft-Day Streamlit App V1 can use local shared
data when available and can fall back to repo-contained sanitized data after a
GitHub pull.

This is not deployment, GitHub Pages, latest_candidate, latest_approved, private
value approval, Mock Draft simulator logic approval, vendor-source approval, or
final trade advice.

## Tim Laptop Start

Pull latest:

```powershell
cd C:\NWR\Niners-War-Room
git fetch origin
git checkout work/hq-parallel-control
git pull --ff-only origin work/hq-parallel-control
```

Open static fallback immediately:

```text
docs\draft_day_exports\final_board_v1_20260622\OPEN_THIS_FIRST.html
```

Start Streamlit:

```powershell
.\scripts\start_draft_day_app.ps1
```

Open:

```text
http://127.0.0.1:8501/rankings
```

If PowerShell is inconvenient, double-click:

```text
START_DRAFT_DAY_APP.bat
```

If Streamlit fails, use:

- `docs\draft_day_exports\final_board_v1_20260622\OPEN_THIS_FIRST.html`
- `docs\draft_day_exports\final_board_v1_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.xlsx`
- `docs\draft_day_exports\final_board_v1_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`

## Data Search Order

Frozen board loader:

1. `NWR_DRAFT_DAY_DATA_ROOT`
2. `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622`
3. `docs\draft_day_exports\final_board_v1_20260622`

App props loader:

1. `NWR_DRAFT_DAY_APP_PROPS_ROOT`
2. `C:\NWR_SHARED_DATA\draft_day_app_props\20260622`
3. `docs\draft_day_exports\final_board_v1_20260622\app_props`

## Repo Fallback Data

Repo fallback path:

`docs\draft_day_exports\final_board_v1_20260622`

Static files present:

- `OPEN_THIS_FIRST.html`
- `index.html`
- `FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- `FINAL_DRAFT_BOARD_V1_FROZEN.xlsx`
- `README_START_HERE.md`
- `LOCAL_ACCESS_INSTRUCTIONS.md`
- `GUARDRAILS_STATUS.md`
- `WHAT_TO_USE_TOMORROW.md`
- `WHAT_NOT_TO_USE_TOMORROW.md`
- `FREEZE_MANIFEST.csv`
- `TRAVEL_START_HERE.md`

Repo-safe app prop fallback:

`docs\draft_day_exports\final_board_v1_20260622\app_props`

Included sanitized prop families:

- `outcome_columns`
- `trading_lab`
- `rookie_hq`
- `mock_draft`
- `decision_board`

The fallback prop files contain no raw vendor rows, raw predictions, hidden sort
fields, or `C:\NWR_SHARED_DATA` path columns.

## Local Shared Data

Local shared source remains supported:

- `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622`
- `C:\NWR_SHARED_DATA\draft_day_app_props\20260622`

Local-only travel zip:

`C:\NWR_SHARED_DATA\draft_day_exports\nwr_draft_day_travel_pack_20260622.zip`

## Smoke Status

- Frozen board row count: 66.
- Repo fallback loader: GREEN.
- Streamlit local URL: `http://127.0.0.1:8501/rankings`.
- All 9 Draft-Day App V1 pages render with the frozen-board source badge.
- Lane prop statuses load as GREEN or clean YELLOW-HOLD states.
- Static fallback files exist.

## Guardrails

- No tuning was rerun.
- No `latest_candidate` or `latest_approved` pointer was updated.
- Frozen board and pinned snapshot were not mutated.
- Mock Draft simulator logic was not changed.
- No deploy, hosted access, public access, GitHub Pages, or new exposed port was created.
- No unsafe `C:\NWR_SHARED_DATA` contents are committed.
- No raw vendor CSVs or raw predictions are committed.
- Frozen Final Draft Board V1 remains the source of truth.
