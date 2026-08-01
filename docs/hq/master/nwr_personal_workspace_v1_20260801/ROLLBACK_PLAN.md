# Rollback plan

The lane is additive. Before canonicalization, remove only the two isolated
Personal Workspace worktrees after resolving their exact paths. After
canonicalization, revert the evidence commit, integration commit, UI commit, and
persistence commit in that order using normal non-force history. Existing user
workspace data is preserved independently and may be exported or restored from a
verified backup. Rollback does not require restoring a formula, rank, active
pack, provider, scheduler, opaque artifact, operational checkout, or Golden
Release state because none changes.
