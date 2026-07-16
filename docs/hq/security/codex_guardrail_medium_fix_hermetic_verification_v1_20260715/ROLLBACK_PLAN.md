# Rollback Plan

Before HQ adoption, delete the isolated branch/worktree or revert the single implementation commit; no remote rollback is needed because Phase 2 does not push.

After canonical adoption, use a normal non-force revert of the implementation commit and the documentation-only canonicalization commit. Re-run the strict Hermetic, exact UI, focused security, PowerShell parse, Ruff differential, and protected-path gates before pushing the revert.

Generated output rollback is limited to bootstrap-owned files beneath an ignored `local_exports/hermetic_test_pack_v1*` root after validating the path prefix. Unowned files must survive. Never remove or alter a LocalData pack, the primary worktree CSVs, scan artifacts, or private evidence.
