# Rollback Plan

The lane is research-only and additive. Before canonicalization, abandon by leaving
the two local commits unadopted. After adoption but before push, reset only the isolated
adoption branch to remote HQ or drop the worktree; never touch preserved worktrees.
After a normal push, create a normal revert of the documentation canonicalization and
its adopted parents. Never force push. Production data/rankings require no rollback
because they were never changed.
