# Rollback plan

There is no production or UI rollout to undo. To remove this research lane,
revert its research/documentation commits or delete its isolated branch and
worktrees. Do not alter Finished V1, Outcome V3, frozen comparator, stable
checkout, operational checkout, persistent state, or scheduled-task state.

If a future independently admitted implementation is built, rollback must
restore the pinned Finished V1 loader, remove dual-lens route/data wiring, keep
Outcome V3 display-only, and verify the immutable hashes before normal push.
Never force push.
