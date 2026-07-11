# Screen-Reader Label Review

Browser accessibility snapshots exposed the following names on both routes:

- `Player from current table`
- `Pick slot`
- `Assign selected player to pick`
- `Undo last assigned pick` (disabled when unavailable)
- `Edit or remove an assigned pick`
- `Show drafted players`
- `Filter and sort players`
- `Draft Board / Pick Tracker`

Visible text repeats the selected player and pick, current pick, current drafting team, drafted count, available count, unavailable reasons, empty state, and draft-complete status. Draft-board state uses literal `Current`, `Open`, and `Drafted` values. Placeholder text is not the sole name of any changed control.

No `aria-label` injection or unsupported custom focus code was added; the implementation relies on Streamlit's native label-to-control mapping observed in the browser accessibility tree.
