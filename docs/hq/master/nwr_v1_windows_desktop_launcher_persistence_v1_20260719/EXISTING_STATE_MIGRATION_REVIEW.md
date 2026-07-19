# Existing-state migration review

Inventory was path/count/size/SHA-256 only before validation. The shared draft root contained 108 files / 726,987 bytes and is reused in place; it was not copied or modified. The Development Lab root and legacy mock-save root were absent.

The primary refresh root contained 40 files / 757,228 bytes. Only the governed latest receipt and accepted receipt backup are eligible. The latest receipt produced `CORRUPT`; the backup was `MISSING`. Therefore:

- original bytes remain at the original path;
- no destination was initialized from them;
- no merge, timestamp choice, quarantine, restore, move, or delete occurred;
- launcher first start returns `BLOCKED_INVALID_LEGACY_STATE`;
- installation verdict is `BLOCKED_NWR_DESKTOP_LAUNCHER_EXISTING_PERSISTENCE_NOT_AVAILABLE`.

For a valid future source, migration first creates a byte-hashed source backup, copies to a staged target, verifies hashes, atomically replaces, and revalidates. Different valid source/target receipts return `BLOCKED_NWR_DESKTOP_LAUNCHER_STATE_MIGRATION_CONFLICT`.
