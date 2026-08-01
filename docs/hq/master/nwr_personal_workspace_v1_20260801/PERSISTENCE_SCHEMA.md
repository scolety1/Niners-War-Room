# Persistence schema

Schema version 1 uses four deterministic JSON stores: `personal_board`,
`decision_journal`, `saved_scenarios`, and `preferences`. Every envelope carries
schema version, store name, UTC update time, payload, and SHA-256 checksum.
Writes use a same-volume temporary file, flush/fsync, and atomic replace under an
exclusive lock. A valid prior store is backed up before replacement. Corrupt,
partial, future-version, unknown-identity, sensitive, recommendation, and
canonical-overlay inputs fail closed.

The default root is `C:\NWR_SHARED_DATA\nwr_personal_workspace_v1`; tests and
demos use `NWR_PERSONAL_WORKSPACE_ROOT`. Protected canonical/source path parts
cannot be selected as a workspace root.
