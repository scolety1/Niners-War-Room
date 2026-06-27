# Dynasty Rankings UX Cleanup

Date: 2026-06-27

## Scope

This lane cleaned up the Dynasty Rankings display and related non-draft backlink clutter. It did not change ranks, tiers, frozen-board data, outcome probabilities, market data, model logic, source-truth gates, Live Draft, Mock Drafts, draft runtime state, draft workflow, pick ownership, or event-log behavior.

## Top Filters Removed From First View

The following controls no longer appear in the main top filter area:

- Tier / Band
- Confidence
- Market match
- Manual review
- Outcome columns

They were moved into an `Advanced filters` expander where useful. The main controls now foreground the basics:

- View preset
- Search
- Position
- NFL Team
- Player type
- Sort
- Ascending
- Age range

## View Presets Added

The page now uses preset lenses:

| Preset | Purpose |
| --- | --- |
| Clean Board | Default full dynasty scan with market basics visible as display-only context. |
| Market Analyzer | Emphasizes DynastyProcess market sanity columns while keeping Dynasty Rank as the default sort. |
| Outcome Lens | Shows only approved committed outcome heads and warns that missing horizons are not available. |
| Data Review | Emphasizes trust, confidence, caveats, and review-needed fields. |
| Compact Draft View | Fast rookie/draft-board scan without changing source data. |

Presets change visible emphasis only. They do not modify data, model values, ranks, hidden sort, or source truth.

## Table Layout And Labels

The table now puts primary football-reading columns first:

- Dynasty Rank
- Player
- Pos
- NFL Team
- Age
- NWR Dynasty Score

When market context is visible, it appears near the score/age area instead of being buried at the far right.

Review-oriented fields move later in the table and use clearer labels:

- `Trust` -> `Data Trust`
- `Key Caveat / Review Flag` -> `Main Caveat`
- `Needs Manual Review` -> `Review Needed`
- `Candidate Band` -> `Value Band (Review-Only)`

Underlying values were not changed.

## Market Display Behavior

Market columns now appear automatically in the main lenses as display-only context. The page and labels continue to state that DynastyProcess/market context does not drive:

- Dynasty Rank
- Candidate Rank
- Final Board Rank
- default sort
- hidden sort
- trade value
- model input

The market registry keeps `sort_allowed=false` and `model_input_allowed=false`.

## Outcome Audit Result

Approved committed outcome heads exist only for:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

The requested horizon fields, including T12 this year, T12 next year, and T12 within next five years, are not present in the approved committed display artifacts. They were not added or faked. Missing outcome data remains `Not enough information`.

Detailed audit:

`docs/hq/app_ux/NWR_DYNASTY_RANKINGS_OUTCOME_COLUMN_AUDIT_20260627.md`

## Back-Link Cleanup

Repeated `Back to Live Draft` links were removed from non-draft research/review/admin pages. Navigation is handled by the main sidebar. Live Draft and Mock Draft draft-room behavior was not changed.

## Guardrails

Confirmed intent:

- Frozen Final Draft Board V1 remains baseline/checkpoint only.
- No `final_board_rank` changes.
- No Dynasty Rank changes.
- No tier assignment changes.
- No pinned snapshot or latest artifact mutation.
- No new outcome model outputs.
- No market/ADP/DynastyProcess model input or hidden sort.
- No CFBD/NFL usage promotion.
- No decision-page wiring.
- No data refresh.
