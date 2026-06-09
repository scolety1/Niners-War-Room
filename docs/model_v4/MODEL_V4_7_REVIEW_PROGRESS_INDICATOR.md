# Model v4.7 Review Progress Indicator

## Goal

Patch the non-blocking v4.6 audit concern that the guided review flow is useful but still heavy for first-time users.

## Changes

- Draft Room now shows a compact progress line before the detailed guide.
- Draft Room detailed guide is now collapsed by default.
- June 15 Review now shows the same compact progress line.
- June 15 detailed guide is now collapsed by default.
- Both guides are grouped into:
  - Start Here
  - Main Review
  - Supporting Context
  - Receipts / Advanced

## Human Review Questions

Each step now names the table to open and the human question to answer later. The guide prepares review only; it does not mark tasks complete, store decision state, or create recommendations.

## Safety

This patch is UI-only. It does not change formulas, scores, output CSVs, active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.
