# Migration, backup, and restore final review

Migration validates the canonical receipt before copy, creates a byte-verified recovery backup first, stages atomically, and validates the migrated result. Invalid legacy or target state and divergent valid receipts fail closed. Missing latest with a valid backup requires explicit recovery. No draft state is treated as a receipt.

Launcher backups are manifest-hashed, bounded to supported state, retained at five generations, created only at a stopped consistency boundary for manual backup, and reject unknown families, unsafe paths, invalid ownership schema, or corrupt hashes. Restore requires exact confirmation, performs dry-run validation, and restores prior exact state on failure, including the empty-state case.
