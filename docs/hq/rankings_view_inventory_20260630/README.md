# Rankings View/Data Inventory Packet V1 - 20260630

This packet documents the current `/rankings` Dynasty Rankings surface so review agents can recommend better preset views, filters, labels, column grouping, and analysis workflows without proposing unsafe model/rank/source-truth changes.

## Current page purpose

`/rankings` is the deep dynasty source board. It starts from the approved current Dynasty Rankings source, enriches it with frozen-board baseline context, display-only DynastyProcess market context, display-only Outcome V1/V2 context, and review-only injury/availability caveats where available.

## Hard guardrails for reviewers

- Do not change Dynasty Rank, Final Board Rank, tiers, frozen board artifacts, pinned snapshots, `latest_candidate`, or `latest_approved`.
- Do not use market/DynastyProcess/ADP values as model input, hidden sort, trade value, pick value, or rank replacement.
- Do not use Outcome V2 as rank logic. Outcome fields are display-only/review-only.
- Do not treat missing Outcome or injury context as low probability, healthy, safe, or clean.
- Do not promote CFBD, NFL usage, vendor, Gmail, proxy, injury, or rookie review data to source truth.

## Current lenses/presets

- Clean Board
- Market Analyzer
- Outcome Lens
- Data Review
- Compact Draft View

## Known display-only/review-only sources

- DynastyProcess market baseline: display-only market context.
- Outcome V1/V2: display-only/review-only context; not rank logic.
- Injury/availability context: review-only caveats, no medical projection.
- Frozen Final Draft Board V1: baseline/checkpoint context only.
- Cross-asset candidate/frozen-board review overlays: review-only context.

## What agents should review

1. Are the five presets the right jobs-to-be-done?
2. Which columns should each preset show or hide?
3. Which labels are too long or confusing?
4. Which filters should be top-level versus advanced?
5. How should market, Outcome, injury, and review caveats be presented so they are useful but not mistaken for source truth?
6. What additional tests or acceptance criteria should protect the guardrails?

## Packet files

- `rankings_presets_inventory.csv`
- `rankings_columns_inventory.csv`
- `rankings_filters_inventory.csv`
- `rankings_data_sources_inventory.csv`
- `rankings_route_label_inventory.csv`
- `rankings_sample_screenshots_or_html_notes.md`
- `protected_path_guardrail_report.md`

## Current data load notes

- Dynasty bundle loaded: `yes`; rows: `240`; source: `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`.
- Frozen board loaded: `yes`; rows: `66`; source: `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv`.
- Unified board rows: `294`.
