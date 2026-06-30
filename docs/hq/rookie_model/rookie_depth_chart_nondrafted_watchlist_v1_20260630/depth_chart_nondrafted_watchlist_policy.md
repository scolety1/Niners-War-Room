# Depth Chart Non-Drafted Watchlist Policy

This is a review-only opportunity-triggered watchlist policy. It is not a UDFA confirmation lane and not a modeling lane.

## Policy

- Most `likely_udfa_needs_review` rows remain ignored or blocked.
- A high depth-chart placement can create a manual review trigger only.
- Depth chart placement does not confirm UDFA status.
- Depth chart placement does not make a row training-safe or model-use approved.
- Current depth chart status is post-draft/current-opportunity context.
- Current depth chart status must not be used as a pre-draft model feature.
- Historical modeling may use depth chart data only if it is point-in-time and available before the relevant prediction date.
- No Gate G, Rankings, Gate F, Live Draft Room, or source-truth wiring is approved.
- Human review is required for any future promotion or source-truth patch.

## Default Thresholds

- QB: depth chart rank <= 2.
- RB: depth chart rank <= 4.
- WR: depth chart rank <= 5.
- TE: depth chart rank <= 2.

If a depth chart source uses text labels rather than numeric ranks, map only clearly parseable labels such as `QB #2`, `RB #4`, `WR #5`, or `TE #2`. Ambiguous text remains `Not enough information`.

## Current Packet Result

No approved populated depth chart rows are available in tracked repo artifacts for this lane. The candidate watchlist is therefore header-only, and missing depth chart data is treated as unknown rather than low opportunity.
