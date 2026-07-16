# Rollback Plan

If push has not occurred, abandon the review branch/worktree; canonical HQ remains unchanged.

After push, create normal non-force reverts in reverse order: first this documentation-only canonicalization commit, then implementation commit `008dd0edc6c71c23784b769aefda124c36fac409`. Re-run security, Hermetic, exact UI, PowerShell, Ruff differential, documentation, and protected/frozen gates before a normal revert push.

Generated Hermetic outputs may be removed only through the bootstrap-owned cleanup contract. Never remove arbitrary `local_exports`, a LocalData pack, scan evidence, primary-worktree CSVs, or private data.
