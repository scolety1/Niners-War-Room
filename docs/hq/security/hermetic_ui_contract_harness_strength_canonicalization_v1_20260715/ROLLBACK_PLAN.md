# Rollback Plan

Rollback readiness: `READY`.

Before push, abandon only the isolated branch and worktree after preserving the
review packet. Do not modify the primary worktree.

After normal HQ push, revert through normal commits; do not reset or rewrite
history. To remove the complete adoption, revert in reverse order:

1. the documentation-only canonicalization commit resolved from the pushed HQ
   tip;
2. `70431d0cfd11ea2f35228453c05e3efcb8a77876`; and
3. `46e334b8ceedfe5d727bff0e084313b4ca09a5cb`.

Rerun the exact nine, all sixteen negative controls, owning/adjacent set,
security byte-identity check, and protected-path scan before any rollback push.
Never force push. The rejected review-evidence commit `e305e6cc` is not part of
the adopted chain and requires no revert.
