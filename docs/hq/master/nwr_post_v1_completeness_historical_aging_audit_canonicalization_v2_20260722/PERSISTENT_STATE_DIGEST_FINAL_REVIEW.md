# Persistent-state digest final review

PERSISTENT_STATE_DIGEST_V1 uses canonical UTF-8 JSON without BOM or terminal
newline. Fixed top-level key order is version, serializer, family, records.
Record key order is path, bytes, sha256. Paths are root-relative POSIX paths,
case-preserving, ordinally sorted, and reject absolute paths, traversal,
duplicates after separator normalization, and inconsistent aliases. Timestamps
are metadata and are excluded from the byte-state digest. SHA-256 is calculated
over the exact serialized bytes.

Independent recomputation from the live hash-only inventories:

- persistent: 14 files, 542,801 bytes,
  88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987
- recovery: 7 files, 172,878 bytes,
  1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835

Both inventories exactly matched every recorded path, size, and per-file hash.
The former aggregate values remain evidence only under
LEGACY_AGGREGATE_METHOD_NOT_REPRODUCIBLE; no historical serializer or command
was found, and the V1 values supplement rather than rewrite the source packet.
