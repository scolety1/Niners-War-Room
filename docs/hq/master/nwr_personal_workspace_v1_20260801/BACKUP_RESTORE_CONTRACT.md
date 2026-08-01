# Backup and restore contract

Workspace backups contain copied store envelopes plus a deterministic inventory
of file name, byte count, and SHA-256. Twenty verified snapshots are retained.
Restore first performs a read-only checksum/schema dry-run, requires explicit
confirmation, creates a safety backup, stages files, and atomically replaces
stores. A corrupt or unsafe backup is blocked; a failed restore rolls back to the
safety snapshot. The launcher performs a fail-closed pre-launch backup.
