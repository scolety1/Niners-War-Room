# Rollback Plan

The Git rollback unit is the CFBD admission commits. Revert normally if review
rejects them; never reset or force-push HQ. The external immutable snapshot is audit
evidence and need not be deleted. Do not alter Finished V1, Outcome V3, the frozen
comparator, persistent/recovery state, or the disabled scheduled task.
