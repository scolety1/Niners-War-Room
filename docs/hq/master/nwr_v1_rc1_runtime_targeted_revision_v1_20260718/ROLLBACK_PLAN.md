# Rollback plan

No successor commit remains after the failed gate; the branch points to RC and all candidate paths are staged. Leave remote branches untouched. Discarding the staged candidate or removing the successor worktree/branch requires a separately authorized recoverable operation.

If a later authorized lane resolves the conflict and adopts a correction, rollback must use a normal non-force revert of that future commit. Do not reset or force push a shared branch. Do not restore, delete, copy, or inspect the five user-owned CSVs. Do not delete LocalData or any unrelated local export.

After rollback, verify `/` still starts, document that `/draft-cockpit-root` is again a known blocker, and rerun Hermetic, LocalData separation, security controls, protected/frozen scan, primary hashes, listener/process cleanup, and route acceptance before any release decision.
