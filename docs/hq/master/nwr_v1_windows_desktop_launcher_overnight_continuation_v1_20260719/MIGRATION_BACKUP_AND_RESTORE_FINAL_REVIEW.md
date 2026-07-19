# Migration, backup, and restore final review

Legacy root `C:\NWR\Niners-War-Room\local_exports\refresh_data` contains 40 files and 757,228 bytes. Metadata and SHA-256 values were recorded without interpreting domain contents. The accepted validator reports the latest receipt `CORRUPT`; no migration, copy, move, quarantine, merge, restore, or overwrite occurred.

Valid future migration is copy-only after a byte-hashed source snapshot; it revalidates destination bytes and accepted receipt semantics. Different valid source/target state fails with `BLOCKED_NWR_DESKTOP_LAUNCHER_STATE_MIGRATION_CONFLICT` and never resolves by timestamp.

Launcher snapshots are staged then atomically finalized, SHA-256 checked, limited to approved families, owner-schema validated, and retained to five valid snapshots. Data Health payloads also pass the accepted receipt validator. Paths reject absolute, anchored, driven, rooted, parent-traversal, symlink/junction escape, and normalized duplicate targets. Manual backup and restore hold the exclusive maintenance lock. Confirmed restore creates a non-prunable pre-restore snapshot, applies an exact supported-file set, validates its final fingerprint, and rolls back exact pre-state on failure. Credentials, LocalData, licensed exports, provider caches, protected CSVs, and browser data are excluded.
