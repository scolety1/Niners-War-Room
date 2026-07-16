# Rollback Plan

Rollback readiness: READY.

Before HQ adoption, reject the branch and remove only the isolated successor
worktree and its branch after preserving review notes. Do not touch the primary
worktree or its five unrelated modified DynastyProcess CSV files.

If HQ later adopts the correction and rollback becomes necessary, create a
normal revert of the single correction commit. Re-run the exact original nine
nodes and the negative-control selection after the revert. Do not use
`git reset --hard`, rewrite history, force push, or apply any separate security
candidate while rolling back this lane.
