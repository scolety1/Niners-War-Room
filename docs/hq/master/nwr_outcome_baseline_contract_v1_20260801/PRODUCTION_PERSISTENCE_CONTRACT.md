# Baseline Production-Persistence Contract

This contract tests persistence mechanics without publishing a production baseline.

1. Input rows must be exact-ID, supported-position, finite NWR-scoring rows at one
   player-season grain.
2. The builder uses only the review replacement ranks in
   `REPLACEMENT_REFERENCE_CONTRACT.csv`.
3. Output is canonical JSON with sorted keys and one LF terminator.
4. The destination is an explicit disposable, nonexistent child directory. Existing,
   non-empty, symlink/reparse, repository, shared-data, LocalData, persistent, recovery,
   and owner-state paths are rejected.
5. Publication writes an exclusive temporary file, flushes it, atomically replaces the
   final file, rereads it, and verifies byte hash and semantic equality.
6. A failed build or reread removes only its disposable temporary file and leaves the
   prior valid artifact untouched.
7. Two independent disposable roots must produce byte-identical output.
8. Production and user-state digests must match before and after the harness.

This contract authorizes only disposable test output. It does not authorize a migration,
production publish, provider call, active-pack update, or page-open write.

