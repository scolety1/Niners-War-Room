# Sprint 5EN-R - Local Visual Smoke Test Execution Handoff

## Purpose

Sprint 5EN-R checks whether an existing local Python environment can run the Streamlit app for the Numeric Outcome Rankings visual smoke test and prepares a final execution handoff for HQ.

This sprint is local review handoff only. It does not deploy, release, merge, push, install packages, create new model outputs, change app/source behavior, change rankings/sorting, create hidden sort keys, or create promoted artifacts.

## Preflight

- Repo path verified: `C:/Users/smcol/Documents/Vacation/Niners-War-Room-outcome`
- Branch verified: `work/outcome-column-gate`
- Recent log includes Sprint 5EN commit: `a23bbe2 Prepare numeric outcome visual smoke test setup`
- Expected dirty state before this doc remained limited to `?? data/`

## Required Checks

Checks completed before environment discovery:

- `python tests\test_nwr_outcome_numeric_probability_display_service.py` - OK
- `python tests\test_nwr_outcome_phase8_status_contract_service.py` - OK
- `python tests\test_nwr_outcome_phase9_status_release_gate.py` - OK
- `python tests\test_dynasty_rankings_page.py` - OK
- `python scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py` - GREEN
- `python scripts\outcome_probability\audit_phase9_outcome_status_release_gate_v1.py` - GREEN
- `python scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py` - GREEN
- `git diff --check` - OK

## Environment Discovery

Repo-local environment files/directories checked:

- `.venv` - missing
- `venv` - missing
- `.conda` - missing
- `.python-version` - missing
- `Makefile` - missing
- `requirements.txt` - present; includes `streamlit`
- `pyproject.toml` - present; includes `streamlit`
- `README.md` - present; documents the app launch command

Existing Python/command checks:

| Candidate | Result |
| --- | --- |
| `C:\Python313\python.exe` | `streamlit_spec=False` |
| `C:\Users\smcol\AppData\Local\Programs\Python\Python311\python.exe` | `streamlit_spec=False` |
| `C:\msys64\ucrt64\bin\python.exe` | `streamlit_spec=False` |
| `streamlit` command | not found on PATH |

No package installation was performed.

## Launch Command

Repo-documented command from `README.md`:

```powershell
streamlit run app/main.py
```

Alternative command if Streamlit is available through an existing interpreter:

```powershell
python -m streamlit run app/main.py
```

## Launch Result

The app was not launched in this sprint.

Blocker:

```text
No existing discovered Python environment has Streamlit installed, and the streamlit command is not available on PATH.
```

No install was attempted.

## Rankings URL

The Rankings route is defined in `app/navigation.py` as:

```text
url_path="rankings"
```

Expected local Rankings URL after successful launch:

```text
http://localhost:8501/rankings
```

Legacy/home aliases that may also route to Rankings:

```text
http://localhost:8501/
http://localhost:8501/home
http://localhost:8501/player-board
```

## Manual Visual Smoke Handoff For HQ

When a Streamlit-capable local environment is available, run:

```powershell
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome"
streamlit run app/main.py
```

Then open:

```text
http://localhost:8501/rankings
```

Manual visual checks:

1. Page loads as `Dynasty Rankings` with no traceback.
2. Outcome columns can be shown from the `Outcome columns` selector.
3. Approved columns only are visible:
   - `QB T12`
   - `RB T12`
   - `RB T24`
   - `WR T12`
   - `WR T24`
   - `WR T36`
   - `TE T12`
4. No Top 6 columns appear.
5. No unapproved heads appear.
6. Unavailable values are honest unavailable/blank/approved fallback values.
7. Unavailable rows do not show fake `0%`.
8. Probabilities are visible only as display-only percentage text.
9. Default ordering is not by probability.
10. No visible or implied hidden Outcome sort key exists.
11. `player_id` is not visible as a column.
12. Rows still match the existing Rankings page pool and filters.
13. Desktop width is usable.
14. Narrow/mobile width is usable if practical.
15. Market, league, ADP, consensus, projection, startup, and trade-calculator context remains display-only.

## Boundary Confirmation

- No deploy occurred.
- No release occurred.
- No merge occurred.
- No branch push or main push occurred.
- No packages were installed.
- No data files were staged or committed.
- No `local_exports/` files were staged or committed.
- No rookie files were touched.
- No new model outputs were created.
- No Top 6 or unapproved heads were created.
- No rankings/sorting changes were created.
- No hidden sort keys were created.
- No promoted artifacts were created.

## Verdict

YELLOW for local visual smoke execution because no existing Streamlit-capable environment was found.

GREEN for 5EN-R handoff documentation and no-install blocker capture.
