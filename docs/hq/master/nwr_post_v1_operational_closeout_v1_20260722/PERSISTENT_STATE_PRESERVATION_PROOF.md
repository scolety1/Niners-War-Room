# Persistent-state preservation proof

Hash-only before/after inventories remained exact:

- persistent: 14 files, 542,801 bytes,
  PERSISTENT_STATE_DIGEST_V1
  88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987;
- recovery: 7 files, 172,878 bytes,
  PERSISTENT_STATE_DIGEST_V1
  1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835.

The manual backup copied two validated state files into the separate bounded
backup root. The restore dry-run reported both targets UNCHANGED. No real-state
restore, refresh, roster hydration, or Trading Lab persistence occurred.
