# Scope-freeze change-control policy

## Admission test

A change after V1 freeze is eligible only if it resolves one of:

1. crash or startup failure;
2. security vulnerability;
3. data-integrity defect;
4. broken supported V1 workflow;
5. materially false trust/freshness state;
6. release-critical accessibility blocker;
7. clean-checkout or Hermetic failure.

All seven classes require reproducible evidence and a focused regression.

## Mandatory rejection

Reject changes that add a feature, source, provider adapter, identity mapping, formula/ranking/recommendation, persistent Trading Lab state, LocalData content, broad redesign, unrelated dependency upgrade, automatic commit/push, or protected/frozen mutation.

## Adoption lane procedure

1. Fetch/prune and rebind to current HQ commit/tree.
2. Inspect every intervening commit for route, formula, identity, source, trust, refresh, security, and protected-path conflicts.
3. Confirm the proposed change qualifies under the admission test.
4. Require narrow diff and named owner.
5. Run affected focused gates, clean Hermetic, LocalData separation, route smoke, Ruff differential, protected proof, and primary-worktree preservation.
6. Obtain independent review.
7. Adopt with a normal commit; never force-push.
8. If any authority question or second correction cycle appears, stop and return the item to post-V1 planning.

No post-freeze feature can be accepted by relabeling it a bug fix.
