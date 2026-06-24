# NWR Cheat Sheet / Tiered Board Polish V2 - 20260623

## Verdict
GREEN.

## Scope
This is a Draft-Day App V2 display/UI polish lane for `/cheat-sheets`. It does not change rankings, source truth, model logic, tier assignments, hidden sort fields, or runtime source artifacts.

## What Changed
- Kept Overall Ranking as the default view.
- Added compact source/status strip with current pick, drafted count, shown row count, source badge language, and display-only ADP reminder.
- Added drafted-player runtime awareness from local V2 live draft state.
- Drafted players are hidden by default with a `Drafted rows` control and `Show drafted` toggle.
- K/DST remain hidden by default with a `Show K/DST` toggle.
- Added secondary position filters.
- Added search and an off-table path to `/player-compare`.
- Added density controls: Compact, Standard, Detailed.
- Added note controls: Summary notes, Detailed notes, Data-health warnings.
- Strengthened tier separators with visible tier headings and player counts.
- Moved source/guardrail details into an expander.

## Default View Behavior
The default view is `Overall Ranking`, sorted by existing `Dynasty Asset Tier/Rank` through the existing workflow service. ADP/market timing context is not the default sort and remains display-only.

## Tier Display
The page groups the visible board by `dynasty_asset_tier` when present, otherwise `final_tier`. The grouping is display-only and does not rewrite tier assignments.

## Runtime Drafted-Player Behavior
The page reads local live runtime state from `C:\NWR_SHARED_DATA\draft_day_runtime\` through the existing runtime service. It does not write runtime state. Drafted players are filtered out by default and become visible only when the user chooses `Show drafted` from `Drafted rows` or turns on the `Show drafted` toggle.

Browser proof on `http://127.0.0.1:8523/cheat-sheets`:
- Default view showed `Current pick: 1.02`, `Drafted: 1`, `Overall Ranking`, `Density`, `Summary notes`, `Position filters`, and visible tier headings.
- Default view hid drafted workflow columns (`Draft Status`, `Assigned Pick`) and filtered out the assigned Tier 1A player.
- Show-drafted view exposed the drafted-row mode and restored the Tier 1A count from 3 to 4, proving runtime drafted-player state can be included.
- `/drafting-mode`, `/live-draft-room`, `/player-compare`, `/trading-lab`, `/mock-draft`, and `/rankings` opened without exceptions.

## Missing Data
Missing values display as `Not enough information`.

## Guardrails
- No Frozen Final Draft Board V1 mutation.
- No `final_board_rank` change.
- No Dynasty Rank overwrite.
- No tier assignment change.
- No latest candidate/latest approved update.
- No pinned snapshot mutation.
- No model/value/ranking logic change.
- No hidden sort fields.
- ADP, market, DynastyProcess, projection, trade calculator, and vendor context remain display-only where shown.

## Remaining Caveats
This lane does not redesign Live Draft Room or Player Compare. It also does not add new data sources or correct upstream data-health gaps.
