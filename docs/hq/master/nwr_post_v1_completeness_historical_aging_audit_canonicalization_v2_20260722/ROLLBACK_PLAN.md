# Rollback plan

Before push, rollback is removal of the isolated adoption branch/worktree only;
source, rejected-review, stable, and primary worktrees remain preserved.

After push, use a normal reviewed revert of the canonicalization commit, then
the harness revision commit, then the two adopted source commits as necessary.
Never force-push or rewrite the branch. Re-run Hermetic, LocalData, ranking
identity, persistent digest, launcher ownership, and Start Here mutation gates
after any rollback. Persistent data requires no restore because adoption did not
change it.
