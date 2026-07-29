# Rollback Plan

Rollback readiness:
`READY_NORMAL_REVERT_NO_DATA_RESTORE`.

If a post-push code rollback is authorized, create normal revert commits for
the documentation canonicalization commit and implementation commit
`9b725b0a57ab1e87c1d69b3053958155eb6bdb5a`. Do not reset or force-push HQ.

The live scheduled task action was not changed and the task remains disabled.
No live refresh ran. No live safe-root generation was published by this lane.
Therefore rollback requires no opaque, board, frozen, persistent, or recovery
data restoration.

Any generations created by a future owner-approved run are immutable. A
rollback must preserve the current generation and pointer until a separately
validated publisher or explicit owner-approved maintenance action selects a
replacement. Cleanup must never delete the pointed-to generation.

The detached review worktree and implementation worktree are retained as
evidence until owner closeout.
