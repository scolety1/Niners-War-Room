# Rollback Plan

This lane creates one local documentation-only commit and no runtime or data state.

If the packet must be rolled back:

1. From the isolated branch, create a normal Git revert of the documentation commit after authorization.
2. Do not reset, rewrite, force push, or alter canonical HQ history.
3. Do not delete or modify LocalData, shared data, snapshots, receipts, or the five primary-worktree CSV modifications.
4. Re-run packet CSV/JSON parsing, manifest validation, protected/frozen hashes, primary hashes, and clean-worktree checks.
5. Remove the isolated worktree only after the user authorizes cleanup and confirms no needed local history remains.

Because no push is authorized, rollback is locally contained. The future implementation design must preserve immutable snapshots and use pointer/receipt rollback rather than overwriting or deleting last-known-good data.
