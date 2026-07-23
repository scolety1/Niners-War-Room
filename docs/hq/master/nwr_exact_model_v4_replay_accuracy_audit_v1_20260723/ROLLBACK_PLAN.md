# Rollback plan

This lane is additive and research-only. To roll it back before adoption, remove
the isolated worktree and branch after independently verifying their exact paths.
To roll back after adopting the local commits, revert the documentation commit
and then the tooling commit. No production state, LocalData, provider state,
rankings, backups, primary opaque CSV, old worktree, or remote branch requires
restoration. No push occurred.
