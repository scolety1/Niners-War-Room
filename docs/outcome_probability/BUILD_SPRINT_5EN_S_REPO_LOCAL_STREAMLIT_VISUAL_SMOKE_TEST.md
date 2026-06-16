# Sprint 5EN-S - Repo-Local Streamlit Visual Smoke Test

## Purpose

Sprint 5EN-S creates a repo-local ignored Python environment, installs only repo-declared dependencies, launches the Streamlit app locally, and verifies the Numeric Outcome columns on the Rankings page without deploying, releasing, pushing, or changing app/source behavior.

## Preflight

- Repo path verified: `C:/Users/smcol/Documents/Vacation/Niners-War-Room-outcome`
- Branch verified: `work/outcome-column-gate`
- Expected dirty state before setup: `?? data/`
- Recent log included Sprint 5EN-R commit: `d298533 Record numeric outcome visual smoke environment blocker`

## Repo-Local Environment

Repo-local venv created:

```text
.venv/
```

Reason for using `.venv/`:

- It is repo-local.
- It is already ignored by `.gitignore`.
- `.venv-outcome-smoke/` is not ignored by the current repo `.gitignore`.

Python and dependency status:

- Python executable: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome\.venv\Scripts\python.exe`
- Python version family: Python 3.13
- Dependency file used: `requirements.txt`
- Streamlit version: `1.58.0`

Install command used:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No global install was performed. No system Python was modified.

## Required Checks

Checks run from the repo-local venv:

- `.\.venv\Scripts\python.exe tests\test_nwr_outcome_numeric_probability_display_service.py` - OK
- `.\.venv\Scripts\python.exe tests\test_nwr_outcome_phase8_status_contract_service.py` - OK
- `.\.venv\Scripts\python.exe tests\test_nwr_outcome_phase9_status_release_gate.py` - OK
- `.\.venv\Scripts\python.exe tests\test_dynasty_rankings_page.py` - OK
- `.\.venv\Scripts\python.exe scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py` - GREEN
- `.\.venv\Scripts\python.exe scripts\outcome_probability\audit_phase9_outcome_status_release_gate_v1.py` - GREEN
- `.\.venv\Scripts\python.exe scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py` - GREEN
- `git diff --check` - OK

## Local App Launch

Repo-documented command from `README.md`:

```powershell
streamlit run app/main.py
```

Repo-local command used:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py --server.headless true --server.address 127.0.0.1 --server.port 8503 --browser.gatherUsageStats false
```

Port note:

- `8501` was already occupied by an existing Streamlit `app/main.py` process using Python 3.11.
- `8502` was already occupied by another existing Streamlit `app/main.py` process using Python 3.11.
- To avoid disrupting those processes, this sprint launched the repo-local venv app on free local port `8503`.

Local URL checked:

```text
http://127.0.0.1:8503/rankings
```

HTTP result:

- `http://127.0.0.1:8503/rankings` returned HTTP 200.

The sprint-owned `8503` Streamlit process was stopped after the smoke checks.

## Smoke Test Method

Browser automation with Playwright was not available in the local Codex Node environment:

```text
playwright_available=false
```

The smoke test used:

- live local Streamlit server at `127.0.0.1:8503`,
- Streamlit's installed testing harness from the repo-local venv,
- the actual `app/pages/05_rankings.py` page,
- the committed app-readable artifact at `app/generated/outcome_probability/numeric_outcome_display_v1.csv`.

This confirmed the page-level UI data contract and table content. Manual browser viewport review remains available to HQ using the same launch command.

## Visual Smoke Results

Streamlit page load:

- `exception_count=0`
- Metrics included:
  - Active players shown: `232`
  - NWR scored: `232`
  - No private score: `8`
  - My Team: `24`
  - Outcome fields: `Display-only`
- Outcome columns selector options:
  - `Compact`
  - `2026 Outcomes`

After selecting `2026 Outcomes`, the main Rankings table had 232 rows and these Outcome columns:

- `QB T12`
- `RB T12`
- `RB T24`
- `WR T12`
- `WR T24`
- `WR T36`
- `TE T12`

Blocked/unapproved columns present:

```text
[]
```

`player_id` visible in main table:

```text
False
```

Default order check:

```text
order_unchanged=True
```

The first 25 rows had the same `Rank`, `Player`, and `Pos` order in Compact mode and in `2026 Outcomes` mode.

Value-format check:

```text
blank_or_percent_values_ok=True
fake_zero_count=0
```

Sample visible values:

| Player | Pos | Outcome values |
| --- | --- | --- |
| Puka Nacua | WR | `WR T12=65%`, `WR T24=86%`, `WR T36=93%` |
| Jaxon Smith-Njigba | WR | `WR T12=61%`, `WR T24=83%`, `WR T36=92%` |
| Bijan Robinson | RB | `RB T12=67%`, `RB T24=84%` |
| Jonathan Taylor | RB | `RB T12=59%`, `RB T24=86%` |
| Jahmyr Gibbs | RB | `RB T12=54%`, `RB T24=75%` |
| Trey McBride | TE | `TE T12=85%` |

## Manual HQ Viewport Follow-Up

Because browser screenshot automation was not available in this environment, HQ can use the repo-local command above to manually confirm:

- normal desktop width is visually usable,
- narrow/mobile width is visually usable if practical,
- the table scroll/width behavior remains acceptable.

The app/content smoke itself was GREEN.

## Boundary Confirmation

- No deploy occurred.
- No release occurred.
- No merge occurred.
- No branch push or main push occurred.
- No packages were installed globally.
- No system Python was modified.
- No data files were staged or committed.
- No `local_exports/` files were staged or committed.
- No rookie files were touched.
- No new model outputs were created.
- No Top 6 or unapproved heads were created.
- No rankings/sorting changes were created.
- No hidden sort keys were created.
- No promoted artifacts were created.

## Verdict

GREEN for Sprint 5EN-S repo-local Streamlit launch and Numeric Outcome Rankings smoke test.
