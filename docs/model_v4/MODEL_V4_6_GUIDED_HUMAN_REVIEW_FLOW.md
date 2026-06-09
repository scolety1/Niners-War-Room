# Model v4.6 Guided Human Review Flow

## Goal

Patch the non-blocking v4.5 audit concern that the app is safe but still heavy for first-time human review.

## Changes

- Added an expanded `Guided review path` section to Draft Room.
- Added an expanded `Guided June 15 review path` section to June 15 Decision Review.
- Kept the existing review-only warning language.
- Did not change formulas, generated scores, output CSVs, active rankings, My Team, War Board, readiness gates, or app promotion.

## Draft Room Review Order

1. Internal Slot: compare rookies, picks, roster players, and context assets on the model's own value scale.
2. Pick Decision Lab: focus on 1.03, 1.04, 2.04, 2.08, and the manual-only 5.04 row.
3. Prospect Board: inspect production, College Team Share, NFL Draft Pick Signal, and Trust.
4. Why This Rank: open when a player looks weird, too high, or too low.
5. Evidence & Risk: check whether the rank is a model edge or a source-risk warning.

## June 15 Review Order

1. Top-Five Drop Decision: confirm the special deadline slot first.
2. Pick & Roster Review: check owned picks, roster pressure, and manual-only 5.04 context.
3. Cut Cost: review what model value would leave the roster if a player is dropped.
4. Trade & Rookie Context: use as supporting context only.
5. Advanced: open receipts, warnings, and raw rows only when needed.

## Safety

All language remains review-only. The patch adds navigation help only and does not create final cut, keep, trade, defer, or draft recommendations.
