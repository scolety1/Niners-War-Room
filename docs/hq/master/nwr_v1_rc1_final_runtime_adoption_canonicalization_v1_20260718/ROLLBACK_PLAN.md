# Rollback plan

The pre-adoption canonical recovery point is:

- commit `7a3d01a5fdd95f4a71d49ced7ff00b334434aa73`;
- tree `b4ab40e584c7c1d39d00f93ee8e5725dc22aafdf`.

Because adoption is a linear three-commit advance, rollback on a shared HQ branch must use normal revert commits in reverse order: this documentation-only canonicalization, `51f2e96bd00ca133abb738b7a1082980b1db979a`, then `c380956dcab863dd7f921ec237506c08f46990b8`. Do not reset or force push. Preserve commit identities and audit history.

Before publishing rollback, fetch/prune, verify live remote ancestry, inspect intervening changes, and stop on conflict. After rollback, rerun Hermetic, LocalData separation, focused security/Data Health/trust/CSV tests, complete route and runtime acceptance, protected/frozen proof, and all five preservation hashes. Verify listeners and Streamlit processes are absent, the worktree is clean, and remote readback matches the intended revert chain.

Do not delete or restore LocalData, runtime exports, primary-worktree CSVs, or unrelated worktrees. Do not create a tag or release as part of rollback.

Result: `ROLLBACK_COMPLETE_AND_NON_FORCE_READY`.
