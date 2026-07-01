# As-Of Guardrail Report

This dataset follows the merged lagged usage as-of policy.

- Feature rows are factual player-week usage rows from admitted 2024-2025 local NFLVerse/Sleeper/public football sources.
- This packet does not declare experiment readiness or production model readiness.
- A future season N to season N+1 builder must aggregate completed season N rows and document the prediction anchor before any experiment gate.
- Current roster, injury, depth, schedule, opponent, next-game, bye, and availability context are excluded.
- Display-safe does not mean model-feature-safe.
