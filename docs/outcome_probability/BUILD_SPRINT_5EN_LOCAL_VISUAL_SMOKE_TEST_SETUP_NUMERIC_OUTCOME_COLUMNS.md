# Sprint 5EN - Local Visual Smoke Test Setup For Numeric Outcome Columns

## Purpose

Sprint 5EN sets up a safe local visual smoke test checklist for the Rankings page numeric Outcome columns after Phase 11 numeric display readiness was pushed to origin.

This sprint is local review planning only. It does not deploy, release, merge, push, create new model outputs, create current-player inference, change app/source behavior, change rankings/sorting, create hidden sort keys, or create promoted artifacts.

## Preflight

- Repo path verified: `C:/Users/smcol/Documents/Vacation/Niners-War-Room-outcome`
- Branch verified: `work/outcome-column-gate`
- Recent log includes latest pushed commit: `2a243a1 Record numeric outcome app display readiness`
- Expected dirty state before this doc remained limited to `?? data/`

## Required Checks

Checks completed before visual setup:

- `python tests\test_nwr_outcome_numeric_probability_display_service.py` - OK
- `python tests\test_nwr_outcome_phase8_status_contract_service.py` - OK
- `python tests\test_nwr_outcome_phase9_status_release_gate.py` - OK
- `python tests\test_dynasty_rankings_page.py` - OK
- `python scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py` - GREEN
- `python scripts\outcome_probability\audit_phase9_outcome_status_release_gate_v1.py` - GREEN
- `python scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py` - GREEN
- `git diff --check` - OK

## Local App Launch Command

Discovered from `README.md`:

```powershell
streamlit run app/main.py
```

The app entrypoint is `app/main.py`.

The Rankings page route is defined in `app/navigation.py` as:

```text
url_path="rankings"
```

Expected local Rankings URL:

```text
http://localhost:8501/rankings
```

Legacy/home aliases that may also route to the Rankings page:

```text
http://localhost:8501/
http://localhost:8501/home
http://localhost:8501/player-board
```

## Launch Status

The app was not launched in this sprint because the active local Python environment does not currently have Streamlit installed:

```text
streamlit_spec False
```

No package installation was performed. A reviewer with the project dependencies already installed can run the command above for the local visual smoke test.

## Visual Smoke Checklist

Open:

```text
http://localhost:8501/rankings
```

Then verify:

1. The page loads as `Dynasty Rankings` with no traceback.
2. The `Outcome columns` selector includes the numeric Outcome group.
3. The numeric Outcome group displays only the approved display columns:
   - QB Top 12 outcome (`QB T12`)
   - RB Top 12 outcome (`RB T12`)
   - RB Top 24 outcome (`RB T24`)
   - WR Top 12 outcome (`WR T12`)
   - WR Top 24 outcome (`WR T24`)
   - WR Top 36 outcome (`WR T36`)
   - TE Top 12 outcome (`TE T12`)
4. No Top 6 columns appear.
5. No unapproved heads appear.
6. Unavailable players show honest unavailable, blank, or approved fallback text.
7. Unavailable players do not show fake `0%` probabilities.
8. Probabilities are display-only text.
9. Sorting does not default to Outcome probabilities.
10. Changing visible columns does not change the existing NWR rank order.
11. No hidden Outcome sort key is visible or implied.
12. Player rows still match the existing Rankings page pool and filters.
13. Outcome values join by `player_id`, not by player name.
14. The `player_id` field is not visible as a column.
15. The page remains usable at normal desktop width.
16. If practical, narrow the browser to mobile width and confirm the table remains usable without traceback.
17. Market, league, ADP, consensus, projection, startup, and trade-calculator context remains display-only.
18. No rookie lane files or rookie framework behavior changed.
19. No deploy, release, merge, main push, or branch push occurs during visual review.

## No-Sorting Review Notes

The visual reviewer should check that the default table order remains driven by the existing Rankings logic. Outcome percentages must not:

- affect private NWR Dynasty Score,
- affect NWR rank,
- affect default sort,
- create visible or hidden sort keys,
- affect player-card decisions,
- affect filters,
- affect league-rank movement.

## Boundary Confirmation

- No app/source files changed in this sprint.
- No data files were staged or committed.
- No `local_exports/` files were staged or committed.
- No rookie files were touched.
- No new model outputs were created.
- No current-player inference was created beyond the already committed app artifact.
- No Top 6 or unapproved heads were created.
- No rankings/sorting changes were created.
- No hidden sort keys were created.
- No promoted artifacts were created.
- No deploy, release, merge, main push, or branch push occurred.

## Verdict

GREEN for local visual smoke test setup documentation.

The actual browser smoke remains pending until a local environment with Streamlit already installed runs:

```powershell
streamlit run app/main.py
```
