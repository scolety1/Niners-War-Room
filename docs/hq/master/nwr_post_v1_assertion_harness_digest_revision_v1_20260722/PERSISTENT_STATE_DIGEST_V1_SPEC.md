# Persistent state digest V1 specification

## Identity

- Digest name: `PERSISTENT_STATE_DIGEST_V1`
- Serializer: `nwr-persistent-state-json-v1`
- Aggregate: lowercase SHA-256 of the exact serialized bytes
- Implementation: `tests/post_v1_assertion_harness.py`

## Inventory record

Each record has exactly `path`, `bytes`, and `sha256` in that key order.

- `path`: root-relative POSIX path after converting `\` to `/`.
- `bytes`: non-negative integer byte size.
- `sha256`: 64-character lowercase SHA-256 of file bytes.
- timestamps: metadata only; never serialized into the byte-state digest.

Absolute paths, drive paths, NUL, empty segments, `.`, and `..` are rejected.
Duplicate normalized paths are rejected, including Windows/POSIX separator
aliases. Case is preserved and compared ordinally, so `A` and `a` are distinct.

## Ordering and serialization

Records are sorted by normalized path using Python string ordinal ordering. The
document keys are exactly `version`, `serializer`, `family`, `records` in that
order. Record keys are exactly `path`, `bytes`, `sha256` in that order.

Serialization is Python `json.dumps` with:

- `ensure_ascii=False`
- `allow_nan=False`
- `separators=(",", ":")`
- UTF-8 encoding
- no BOM
- no trailing newline
- no insignificant whitespace
- no self-hash field

The family identifier is lower-case ASCII `[a-z0-9][a-z0-9._-]*`. An empty
inventory serializes normally with `"records":[]` and therefore has a defined
digest.

## Exact reproduction command

From the repository root:

```powershell
& 'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe' -c "import sys; from pathlib import Path; sys.path.insert(0,'tests'); from post_v1_assertion_harness import digest_records_from_csv,persistent_state_digest_v1; p=Path('docs/hq/master/nwr_post_v1_assertion_harness_digest_revision_v1_20260722/PERSISTENT_STATE_DIGEST_REPRODUCTION.csv'); print(persistent_state_digest_v1(digest_records_from_csv(p,family='persistent'),family='persistent')); print(persistent_state_digest_v1(digest_records_from_csv(p,family='recovery'),family='recovery'))"
```

Expected output, in order:

```text
88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987
1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835
```

Tests cover deterministic rerun, reverse order, separator normalization,
duplicates, case, empty inventory, byte and size changes, timestamp-only change,
traversal/absolute paths, non-ASCII path, and one-file addition/removal.
