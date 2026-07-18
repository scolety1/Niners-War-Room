# Validate Before Mutate Proof

The writer first builds and fully preflights a provisional candidate without reading or
touching storage. It validates the narrow input, exact keys/types/enums, flat result shape,
privacy, cross-field relationships, closed v2 document, integrity-free deterministic body,
SHA-256 metadata, exact final serialization, and 2 MiB limit.

Only then does it inspect latest and backup read-only, incorporate a validated v2 prior
relationship, and repeat the entire finalization and size check. No directory is created and
no temporary is opened before both preflights pass.

For commit, all same-root temporary files are fully written, flushed, and fsynced before any
target changes. The order is prior-valid backup, candidate archive, conditional invalid-prior
quarantine evidence, and latest last. Retention deletions are precomputed and included in the
rollback snapshot. On any exception, every changed or deleted target is restored from exact
captured bytes and its mtime is restored; newly created targets and temporaries are removed.

Evidence:

- 21 parameterized invalid candidates preserve a complete tree snapshot.
- Oversized final serialization preserves the tree.
- A 257-row input preserves the tree.
- A synthetic failure at latest replacement restores backup/archive/latest and leaves no
  temporary.
- Tree snapshots contain directory entries plus every file's length, SHA-256, and mtime_ns.
