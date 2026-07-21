# Rollback and icon removal plan

1. Create a normal revert commit for the single implementation commit; never reset or force push the shared branch.
2. Fetch and verify canonical remote identity, then fast-forward the stable checkout to the reverted commit.
3. Run the reverted canonical installer from the exact clean stable checkout so the two primary shortcuts return to its authorized icon contract.
4. Validate shortcut target, arguments, working directory, description, and icon metadata.
5. Request only a bounded shell icon refresh if needed.
6. Re-run launch, rankings, Stop, port, ownership, Hermetic, LocalData, persistence, primary-hash, and protected/frozen gates.

Rollback must not delete LocalData, persistent data, backups, recovery quarantine, draft state, the five primary CSVs, unrelated shortcuts, worktrees, or the global Windows icon cache. Explorer restart, sign-out, or reboot remains a manual user choice only if Windows continues to display a cached image.
