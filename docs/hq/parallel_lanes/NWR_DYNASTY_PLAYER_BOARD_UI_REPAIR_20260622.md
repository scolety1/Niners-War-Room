# NWR Dynasty Rankings Player Board UI Repair - 2026-06-22

## Verdict

GREEN. This repair is UI/display-only. It does not change Dynasty Rank values, Final Board Rank, model/value logic, latest_candidate, latest_approved, the pinned snapshot, or the frozen 66-row board.

## Clutter Removed Or Collapsed

- Removed the large metric-card block from the main top area.
- Removed long source/hash/proof-row captions from the main page flow.
- Removed long Outcome coverage paragraphs from above the table.
- Moved source paths, hashes, warnings, errors, draft-board-only counts, Outcome support, and age support into a collapsed `Source / diagnostics` expander.
- Kept only compact header chips for:
  - Full dynasty rows: 240
  - Frozen board rows: 66
  - Outcome support: 12/66

## Default Table/View Before And After

Before:

- Defaulted to a unified review surface.
- Foregrounded `Final Board Rank`, `Final Tier`, and `Source Coverage`.
- Table appeared after banners, metric cards, proof rows, and collapsed filters.
- Looked too much like Live Draft Room.

After:

- Defaults to `Full Dynasty Rankings`.
- Sorts by `Dynasty Rank` ascending.
- Table appears immediately after compact filters.
- `Puka Nacua` Dynasty Rank 1 sorts above `Zay Flowers` Dynasty Rank 12.
- `Final Board Rank` and `Final Tier` are not in the default Full Dynasty display.
- `Source Coverage` is not a leading/default column.

## Full Dynasty View Columns

Default Full Dynasty view columns:

- Dynasty Rank
- Player
- Pos
- NFL Team
- Age
- Position Rank
- Asset Type
- NWR Dynasty Score
- Trust
- Warnings
- Status
- Data Needed
- Outcome Display-Only columns

Outcome columns remain display-only and do not drive default sort.

## Rookies / Draft Board View Columns

Default Rookies / Draft Board columns:

- Final Board Rank
- Player
- Pos
- NFL Team
- Age
- Final Tier
- Asset Type
- Board Availability
- Draft Action (Display-Only)
- Dynasty Rank
- Outcome Display-Only columns

This view defaults to Final Board Rank ascending and is where draft-board-only rookies/prospects are easiest to review.

## Filters Added

Visible compact filters above the table:

- Search player
- Position multi-select
- Source / player type
- NFL Team
- Outcome availability
- Sort by
- Ascending toggle
- Age range if supported by source data

Current age source has no supported numeric values, so the page shows `Age filter: Not enough information` instead of fabricating an age range.

## Age Source And Missing Count

Age source:

- Approved full dynasty rankings artifact column: `age`.
- Frozen board did not provide an age column.
- Live Draft Room now receives a display-only `Age` column from the frozen board loader.

Current support:

- Supported numeric age rows: 0
- Missing age rows in unified board: 294
- Display value for missing age: `Not enough information`

The age formatter is ready to display supported numeric ages to one decimal, but the current approved source is blank.

## Proof Rookies Are Accessible

- `Rookies / Draft Board` view shows 66 frozen board rows.
- Draft-board rookie/prospect rows available: 54.
- Browser proof showed `Rows shown: 66 | View: Rookies / Draft Board | Sort: Final Board Rank`.

## Proof Default Dynasty Order Is Correct

Service-level proof from the approved full dynasty source:

- Full Dynasty rows: 240
- Puka Nacua Dynasty Rank: 1
- Zay Flowers Dynasty Rank: 12
- Puka Nacua sorts before Zay Flowers in the Full Dynasty view.

Browser proof:

- `/rankings` opens cleanly.
- Default view shows `Rows shown: 240 | View: Full Dynasty Rankings | Sort: Dynasty Rank`.
- Compact filters are visible before the table.
- Default visible page flow no longer foregrounds Final Board Rank or Final Tier before diagnostics.

## Live Draft Room Age

Live Draft Room table display columns now include Age after NFL Team:

- Draft Status
- Assigned Pick
- Final Board Rank
- Player
- Pos
- NFL Team
- Age
- Asset Type
- Board Availability
- Draft Action (Display-Only)

Current Live Draft age values are `Not enough information` because the approved sources do not provide numeric age values.

## Remaining YELLOW/RED

- YELLOW: Browser automation could not reliably trigger Streamlit text-entry reruns for the search box, although the search control is visible and the filter logic is implemented in the page code.
- YELLOW: Current approved age source is blank, so the app cannot show real ages yet.
- GREEN: No rank/source/model mutations were made.
