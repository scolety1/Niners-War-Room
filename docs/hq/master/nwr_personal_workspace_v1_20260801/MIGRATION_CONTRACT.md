# Migration contract

Migration preflights the current version, all store checksums, free disk space,
exclusive lock, and pre-migration inventory digest. It creates and verifies a
full workspace backup before writing the additive schema marker, then writes an
auditable receipt. Future schema versions, corruption, insufficient space,
lock contention, or backup failure block. Injected failure after backup restores
the prior schema state and writes an external rollback receipt.
