# Primary and persistent state preservation

The five user-owned DynastyProcess CSVs in the primary worktree are treated as
opaque and are checked only by their supplied SHA-256 values at every required
checkpoint. They are never parsed, copied, normalized, staged, or committed.
All five hashes remained exact at lane start, after receipt recovery, after
historical evaluation, before and after the tooling commit, and before the audit
commit.

Persistent product state baseline: 14 files / 542,801 bytes /
PERSISTENT_STATE_DIGEST_V1
`88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`.
Recovery baseline: 7 files / 172,878 bytes /
PERSISTENT_STATE_DIGEST_V1
`1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.

Metadata-only file-by-file size and SHA-256 checks reproduced both baselines
without interpreting their contents. No persistent state, backup, quarantine,
old worktree, stable checkout, or primary file was written.
