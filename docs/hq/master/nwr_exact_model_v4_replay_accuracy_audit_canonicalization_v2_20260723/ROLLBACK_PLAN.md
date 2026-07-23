# Rollback plan

Rollback is ordinary, non-destructive Git history management. Revert the
documentation-only canonicalization commit first. If the bounded assertion
revision must also be removed, revert
`5fb7339e45c3536b9d4ec9bfce1b2afc302a41d3`, then the original audit
`0929ce6ec058a698efeee10fe5770f56047bab21`, then the original tooling
`bfb1a489741250d7fa63c9b134fd007dbbfa841d`, in reverse order.

Do not reset or force push. Do not delete preserved worktrees. Do not restore,
rewrite, or delete primary, persistent, backup, recovery, browser-profile, or
LocalData state. Production rankings and frozen artifacts require no data
rollback because they were never changed.
