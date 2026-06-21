# Niners War Room Draft-Day Travel Start Here

Use this after pulling the repo on Tim's laptop.

## 1. Pull Latest

```powershell
cd C:\NWR\Niners-War-Room
git fetch origin
git checkout work/hq-parallel-control
git pull --ff-only origin work/hq-parallel-control
```

## 2. Static Fallback Works Immediately

Open:

```text
docs\draft_day_exports\final_board_v1_20260622\OPEN_THIS_FIRST.html
```

Spreadsheet fallback:

```text
docs\draft_day_exports\final_board_v1_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.xlsx
```

## 3. Start Streamlit

Run from repo root:

```powershell
.\scripts\start_draft_day_app.ps1
```

Or double-click:

```text
START_DRAFT_DAY_APP.bat
```

Then open:

```text
http://127.0.0.1:8501/rankings
```

## 4. If Streamlit Fails

Use the static fallback and spreadsheet above. The repo contains the sanitized
frozen board and app prop fallbacks needed for offline review.

## Guardrails

This is local-only draft-day review access. It is not hosted deployment,
latest_approved, private value approval, Mock Draft logic mutation, vendor-source
approval, or final trade advice.
