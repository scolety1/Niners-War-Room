# Dynasty Rankings Outcome Column Audit

Date: 2026-06-27

## Verdict

Outcome columns may be displayed only from the existing approved display artifacts. No new outcome probabilities, horizons, or model outputs were created for this UX pass.

## Current Outcome Fields

The current approved display artifact is:

`docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns/outcome_column_metadata.csv`

It approves these display-only heads:

| Field | Position Scope | Status |
| --- | --- | --- |
| QB T12 | QB | Available as display-only |
| RB T12 | RB | Available as display-only |
| RB T24 | RB | Available as display-only |
| WR T12 | WR | Available as display-only |
| WR T24 | WR | Available as display-only |
| WR T36 | WR | Available as display-only |
| TE T12 | TE | Available as display-only |

The app service mirrors those same fields through `APPROVED_OUTCOME_DISPLAY_FIELDS`.

## Requested Original/Planned Fields

The user requested an audit against concepts such as:

- T12 this year
- T12 next year
- T12 within next five years
- T6/T24/T36 by position if those existed in approved artifacts/docs

The current committed display metadata does not contain explicit `this year`, `next year`, or `next five years` horizon columns. Older legacy page text referenced horizon-style placeholder labels, but those were not backed by approved committed display values and must not be revived as real columns.

## Safe-To-Display Fields Now

Safe to display now, as review/display-only:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

These fields must remain display-only and cannot drive sort, rank, model value, Candidate Rank, draft actions, or hidden prioritization.

## Missing / Blocked Fields

Blocked until an approved artifact exists:

- T12 this year
- T12 next year
- T12 within next five years
- QB T6 / QB T24 / QB T36
- RB T6 / RB T36
- WR T6
- TE T6 / TE T24 / TE T36

Missing outcome data must display as `Not enough information`, never as zero probability, low probability, clean health, low risk, or a hidden penalty.

## Page Policy

Dynasty Rankings may expose the approved current outcome heads in an `Outcome Lens` view/preset. If a requested horizon is missing, the UI should say so plainly instead of creating a fake column.
