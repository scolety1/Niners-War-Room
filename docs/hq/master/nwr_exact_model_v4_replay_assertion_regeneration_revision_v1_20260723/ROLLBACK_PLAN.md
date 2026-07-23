# Rollback plan

Before adoption, remove only the isolated successor branch/worktree after exact
path verification. After adoption, revert the single revision commit, then the
original audit and tooling commits in reverse order if complete rollback is
required.

Rollback never edits production state, rankings, frozen inputs, LocalData,
backups, recovery, the primary opaque CSVs, or any preserved worktree. The
canonical source commit, manifests, hashes, and normal-push commit chain provide
the readback authority. No force push is permitted.
