# NWR Overnight Run Recommendation

## Recommended Overnight Task

`Model v4 Historical Receipt Locator and Ledger V1`

## Why This Task

This is the safest overnight task because it advances the main blocker without running Formula Gauntlet, tuning formulas, changing rankings, or promoting sources. The current bottleneck is not lack of ideas. It is missing season-by-season receipt visibility for the exact Model v4 chain.

## Objective

Locate and ledger season-by-season equivalents of:

- `current_value_full_board_review_rows`
- `current_player_value_full_board_review_rows`

The ledger should record:

- source path
- original worktree or archive
- SHA256
- schema
- row count
- season range
- position coverage
- identity fields
- use gate
- decision-date safety
- leakage risk
- whether it supports exact replay, partial replay, or component signal tests

## Explicitly Not Recommended

- Full system audit only: completed by this packet.
- Review-only component signal tests: possible later, but still needs execution contract.
- 100-candidate review-only Formula Gauntlet smoke run: not allowed.
- Formula Gauntlet candidate arena: not allowed.
- Champion refinement: not allowed.
- No overnight run: acceptable if avoiding lane churn, but locator/ledger is the best safe progress.

## Stop Conditions

Stop if the lane would need to copy raw recovered local artifacts into canonical docs, regenerate model outputs, run benchmark logic, calculate formulas, or alter rankings/app/runtime behavior.
