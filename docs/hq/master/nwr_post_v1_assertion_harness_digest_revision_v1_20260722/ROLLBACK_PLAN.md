# Rollback plan

The revision is one tests-and-documentation commit on top of `18c63e96`.

Before adoption, abandon the successor branch and retain the source/rejected
worktrees unchanged. After adoption, revert the targeted harness commit with a
normal revert if necessary; do not reset HQ, force-push, or alter persistent state.
The website and research source commits remain independently identifiable.

Digest V1 is supplementary documentation. Rollback never changes the 14-file or
7-file state inventories and never attempts to recreate a legacy aggregate.
