# Final Index and Tree Binding Contract

1. Capture repository root, parent, named branch, remote name, and exact remote URL before the worker starts.
2. Stage the complete candidate with `git add --all -- .` before each approval gate. This admits pre-staged and intended non-ignored untracked content.
3. Require zero unstaged tracked drift and zero non-ignored untracked drift.
4. Review only `git diff --cached HEAD --` and record `git write-tree`.
5. Freeze the approval tuple: repository root, parent, branch, remote, remote URL, approved tree, privilege booleans, and trusted-envelope digest.
6. Abort if any tuple member, candidate byte, index tree, tracked worktree, or untracked inventory changes.
7. The production supervisor stops at `APPROVED_DRY_RUN` and leaves the index staged. It does not call the isolated commit helper.

The positive commit-tree and push-binding controls operate only in disposable repositories and remotes. They prove the helper can commit exactly the approved tree with exactly the approved parent and rejects every mismatched tuple.
