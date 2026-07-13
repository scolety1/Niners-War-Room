# Rollback Plan

## Unit

Rollback the one local Player Compare accessibility/compact commit. Do not reset or rewrite HQ history.

## Procedure

1. In an HQ review worktree, verify the lane commit is the only commit being reverted.
2. Run `git revert <lane-commit>` to create a normal inverse commit; never force push.
3. Confirm removal of the Player Compare helper import/call, semantic/region headings, selector-label changes, selected-context call, and trust/how-to-use relocation.
4. Confirm deletion of `app/components/player_compare_accessibility.py`, the focused test/fixture files, and this packet if the complete lane is being withdrawn.
5. Rerun Player Compare, Decision Trust Strip, comparison-service, navigation, and route smoke regressions.
6. Reconfirm `app/components/decision_trust_strip.py`, `src/services/decision_trust_strip_service.py`, production data, Trading Lab, and frozen artifacts remain byte-identical to the controlling HQ state.

## Safety

The rollback does not require data migration, persistence cleanup, identifier conversion, cache invalidation, formula reversal, source-registry change, or frozen-artifact repair. The lane creates no runtime data and no external state.
