# Uninstall, backup, and recovery guide

`scripts\Uninstall Niners War Room Shortcut.ps1` removes only a shortcut whose exact target, arguments, working directory, description, supported runtime, and interactive identity match the launcher. It preserves `%LOCALAPPDATA%\NinersWarRoom`, shared draft state, backups, logs, and browser profile.

Use `scripts\NWR Desktop Commands.ps1 backup` only while NWR is stopped. Use `restore-dry-run <snapshot-id>` before `restore <snapshot-id> --confirm <snapshot-id>`. Restore rejects invalid families, paths, hashes, schemas, accepted receipt semantics, and corrupt backups; it holds the maintenance lock and creates an exact rollback snapshot. Never manually copy LocalData, credentials, provider payloads, or protected CSVs into a snapshot.
