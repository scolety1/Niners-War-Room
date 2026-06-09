# Model v4.5 Phase 5: Clean Naming And Warning Cleanup

## Goal

Make the finished review-only decision systems easier to read without changing formulas, scores, active rankings, My Team, War Board, readiness gates, or app promotion.

## Label Cleanup

The app display layer now uses consistent human-facing names:

- `allowed_use` -> `Use`
- `blocked_use` -> `Blocked`
- `confidence_cap` -> `Trust Cap`
- `market_share_score` -> `College Team Share`
- `draft_capital_score` -> `NFL Draft Pick Signal`
- `source_risk_level` -> `Evidence Risk`
- `model_edge_weirdness` -> `Model Edge`
- `source_shape_warning` -> `Data Shape Warning`
- `format_discipline_case` -> `Format Discipline`

The underlying CSV fields and raw warning codes are preserved in receipts, component rows, warnings tabs, and exports.

## Warning Group Cleanup

Default Draft Room and June 15 tables now surface warning groups before detailed codes:

- Data incomplete
- Low draft investment
- No-premium TE caution
- 1QB QB caution
- Source-limited role data
- Manual review required

Detailed warning text remains visible beside the grouped summary where useful. Raw codes remain available in drilldown tables and export files.

## App Surfaces Updated

- Draft Room prospect board
- Internal Slot / Startup Slot Simulator
- Pick Decision Lab
- Historical Comps
- Evidence Risk / Source Risk Heatmap
- Model Edges
- Rookie scout queue
- June 15 Review cards
- June 15 Cut Cost table
- Supporting filters for Evidence Risk and Model Edges

## Safety

- No score formulas changed.
- No generated private football value changed.
- No market, ADP, ranking, projection, mock draft, big-board, or consensus input was added.
- No final cut, keep, trade, draft, or roster recommendations were created.
- Review-only restrictions remain visible in raw outputs and drilldowns.

## Tests

Added static checks proving:

- The required display-label mapping exists.
- Default tables use warning groups and warning details.
- Raw warning fields remain available.
- No final-action directive language was introduced.

## Patch Pass

The Phase 5 patch pass also renamed remaining filter/control language:

- `Risk Level` -> `Evidence Risk`
- `Classification` -> `Edge Type`
- `Weirdness Type` -> `Why It Is Unusual`
- `Feature Rows` -> `Raw Feature Rows`
