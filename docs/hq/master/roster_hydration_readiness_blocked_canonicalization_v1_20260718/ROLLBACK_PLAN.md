# Rollback Plan

This lane adds two documentation commits above starting HQ: the preserved source readiness commit and the canonicalization/parking commit. It adds no application behavior, data migration, production data, LocalData, configuration, identity rows, provider state, or external side effect.

If rollback is required after publication, Master HQ may create a normal review branch from the then-current remote and revert the canonicalization commit, then separately revert the preserved source commit if the readiness packet itself must be removed. Do not rewrite history and do not force push.

Rollback must not alter or delete the primary worktree's five DynastyProcess CSV modifications. It requires no LocalData deletion and no provider action. Any later post-V1 implementation must have its own rollback plan and cannot rely on this documentation rollback.
