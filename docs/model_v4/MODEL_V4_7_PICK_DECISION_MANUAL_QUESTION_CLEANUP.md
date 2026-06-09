# Model v4.7 Pick Decision Manual Question Cleanup

## Goal

Patch the non-blocking v4.6 audit concern that Pick Decision Lab `manual_questions` could be too long for quick export review.

## Changes

Added structured manual-question fields to `pick_decision_rows.csv`:

- `manual_question_rookie_profile`
- `manual_question_roster_fit`
- `manual_question_pick_value`
- `manual_question_trade_defer`
- `manual_question_source_risk`

The original `manual_questions` field remains for backwards compatibility.

## UI

Draft Room -> Pick Decision Lab now displays the structured question fields instead of one long Manual Questions column.

## 2026 5.04

The 2026 5.04 row remains `manual_only_no_exact_model_baseline`. Its pick-value question explicitly states that no admitted exact model baseline exists and that the row is manual-only watchlist review.

## Safety

This patch changes readability only. It does not create final draft recommendations, alter formulas, change scores, mutate active rankings, My Team, War Board, readiness gates, or app promotion.
