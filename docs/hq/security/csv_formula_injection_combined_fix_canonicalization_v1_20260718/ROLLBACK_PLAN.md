# Rollback Plan

The adopted history remains three separately addressable commits: original
fix, correction, and documentation-only canonicalization. It is not squashed,
amended, or rewritten.

If rollback is required after HQ adoption:

1. Fetch and verify the live `work/hq-parallel-control` identity.
2. Create an isolated rollback worktree and branch at live HQ.
3. Revert the documentation-only canonicalization commit first.
4. Revert `65a378949a3df7875fc24458c276b7bdf1537916` second.
5. Revert `27ed532b01ddb7fc307a489b0c5bd6332ee70f4f` only if the complete CSV
   formula-injection protection must be removed.
6. Rerun the focused, Hermetic, LocalData-contract, Ruff differential,
   protected/frozen, security-automation, Git-integrity, and five hash-only
   preservation gates.
7. Push only by a normal non-force update after independent authorization.

The pre-adoption anchor is
`46d0f40eb5f1b00a7a993ed90958d37461aaa1b5`, tree
`487797f692ec132ad32c95044fdb810cfc3e33a1`. Revert commits are preferred over
history rewriting so the reviewed chain and audit trail remain recoverable.
