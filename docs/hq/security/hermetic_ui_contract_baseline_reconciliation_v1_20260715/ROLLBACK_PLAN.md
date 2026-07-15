# Rollback Plan

No push or merge was performed. Rollback is fully local.

Preferred HQ-review options:

1. Reject the branch and remove only the isolated worktree and successor branch after preserving any review notes.
2. If the local commit was adopted and later must be undone, create a normal revert of that single commit.
3. Re-run the exact nine-node set after rollback; the clean-HQ baseline should return to `6 failed, 3 passed`, proving removal of this reconciliation.

Do not use `git reset --hard` in the primary repository worktree. Do not touch the five unrelated modified DynastyProcess CSVs. Do not revert or apply the separate security candidate while rolling back this lane.

Rollback readiness: READY.
