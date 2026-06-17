# Deployment V2 Local Streamlit UI Label Visual Check Guide

## Scope

This guide is for non-technical local operators checking the Niners War Room V1
Streamlit app after it starts locally. It is text-only. No screenshots were
captured in this sprint, and this guide does not change app behavior.

This is not hosted deployment approval. It does not create a deploy command,
public app, public port, tunnel, secret, container, or CI/CD workflow.

## Where To Go After Launch

After starting the app with:

```powershell
streamlit run app/main.py
```

open the Rankings page:

```text
http://localhost:8501/rankings
```

If Streamlit prints a different local port, use that port and add `/rankings`.
For example:

```text
http://localhost:8502/rankings
```

## Expected Page Context

The operator should be on the Rankings page.

If there is a view, tab, selector, or column option for 2026 Outcomes, choose the
view that shows the V1 Outcome numeric columns. If the Rankings table appears
but Outcome columns are not visible, stop and ask HQ before changing app code or
data.

## Approved Outcome Labels To Look For

Only these Outcome labels are approved for V1 local operator checks:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

The table does not need to show every label on every player. Position-specific
columns may be blank, unavailable, or not applicable for players at other
positions.

## Labels Or Columns That Should Not Appear

Stop and ask HQ if any of these appear as visible table columns or Outcome
heads:

- Top 6
- unapproved Outcome heads
- `player_id`
- hidden sort-key columns
- internal-only sort columns
- promoted artifact indicators

Outcome columns must not change player ranking order or sorting.

## How Percentages Should Look

Readable percentages should look like display values for a human review table,
for example:

- `24%`
- `24.3%`
- blank
- `unavailable`
- `n/a`

The operator should not see raw internal probability field names, hidden model
keys, or long unformatted decimal values in normal local operation.

## How Unavailable Players Should Look

Unavailable or inapplicable players should not show fake precision.

Acceptable unavailable display examples:

- blank cell
- `unavailable`
- `n/a`
- a clear fallback label

Stop and ask HQ if unavailable or inapplicable rows show fake `0%` values that
look like real measured probabilities.

## Signs The Page Likely Loaded Correctly

The page likely loaded correctly if:

1. The browser uses a local URL such as `localhost` or `127.0.0.1`.
2. The Rankings page opens without a Python traceback.
3. The Rankings table renders.
4. Player names and positions are visible.
5. Approved Outcome labels appear only as listed above.
6. No Top 6 or unapproved heads appear.
7. No hidden sort-key columns appear.
8. Sorting/ranking appears unchanged by the Outcome columns.

## When To Stop And Ask HQ

Stop and ask HQ if:

- the browser URL is not local
- Streamlit shows a Python traceback
- the Rankings page does not open
- the Rankings table is empty when it should have players
- Outcome labels are missing from the expected local view
- Top 6 or unapproved heads appear
- hidden sort-key columns appear
- player ranking order appears changed by Outcome columns
- unavailable rows show fake precise percentages
- the operator is unsure which local folder or branch is being used

Do not fix these issues by changing app code, data, Outcome behavior, or
rankings in the Deployment V2 lane.

## Future Screenshot Placeholders

No screenshots were captured in this sprint.

Future screenshot slots, if HQ approves a screenshot sprint:

1. Local Streamlit startup terminal with local URL visible.
2. Rankings page landing state.
3. 2026 Outcomes view or column selector, if present.
4. Approved Outcome labels visible in the Rankings table.
5. Example unavailable/fallback cells.

Screenshots would be documentation aids only. They would not approve hosted
deployment or app behavior changes.

## Local-Only Reminder

This guide supports local-only operator checks. Hosted deployment remains
blocked. Do not create deploy commands, expose public ports, create secrets,
push, deploy, or commit `.venv/`, `data/`, or `local_exports/`.
