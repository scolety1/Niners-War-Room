# Rollback Plan

This optional lane is local-only. Before any future push, abandon the isolated
branch/worktree to leave canonical HQ unchanged.

If a future authorized integration has already occurred, create a normal
non-force revert of the integration commit. Re-run the paired exploit PoC,
focused 92-test set, strict Hermetic tier, LocalData gate, changed-file Ruff,
and protected-path review before any normal revert push.

Do not reset, stash, clean, amend, force-push, or modify the primary worktree.
Do not remove owner-authorized LocalData or unrelated user CSV changes.
