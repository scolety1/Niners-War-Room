# Rollback plan

Rollback is code-and-packet-only:

1. Revert the Outcome V3 implementation commit(s) normally.
2. Remove the compact Rankings lens and expanded Player Compare V3 adapter by
   that revert.
3. The pre-existing Outcome V1/V2 loaders and aliases resume as the only
   Outcome display.

No data migration, ranking rebuild, persistent-state repair, provider call,
refresh, or scheduled-task change is required. Never force push.
