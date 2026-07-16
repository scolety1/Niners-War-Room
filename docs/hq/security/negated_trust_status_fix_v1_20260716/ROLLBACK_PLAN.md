# Rollback Plan

This branch is local-only. Before future integration, abandoning the isolated
branch/worktree leaves canonical HQ unchanged.

If a separately authorized integration later occurs, create a normal non-force
revert of its commit. Re-run the original safe PoC, 26-test security matrix,
78-test ownership set, exact nine UI nodes, strict Hermetic tier, LocalData gate,
Ruff differential, and protected-path review before any normal revert push.

Do not reset, stash, clean, amend, force-push, or alter the primary worktree.
