# Opaque and persistent state preservation

Opaque DynastyProcess files were not opened, parsed, copied, normalized, staged,
or used. The existing preservation checker was used only for byte counts and
hashes.

- opaque hash matches: `5/5`;
- persistent: `14` files /
  `542801` bytes /
  `88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`;
- recovery: `7` files /
  `172878` bytes /
  `1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`;
- evidence status: `PASS_SETUP_HASH_ONLY`.

Tracked review-only sidecars are used only at their governed classification and
do not grant authority to their historical upstream source.
