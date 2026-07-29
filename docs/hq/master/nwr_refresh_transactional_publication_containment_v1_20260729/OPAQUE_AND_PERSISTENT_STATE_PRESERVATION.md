# Opaque and Persistent State Preservation

Opaque status:
`OPAQUE_BASELINE_ADVANCED_AFTER_PROVEN_AUTOMATED_REGENERATION_NO_CONTENT_ADMISSION`.

The five live primary-local opaque files were verified only by SHA-256. They
were not parsed, copied, summarized, or admitted:

- `dp_freshness_report.csv`:
  `f34b88e4d0486ec7e34a6e74e1e8953147f91a7b67237062bac0e451eb180e59`
- `dp_market_baseline_context.csv`:
  `a477c6742e14ac4fd6a892b1f56807a0475c62254f632097a03198b303909bbf`
- `dp_nwr_join_coverage.csv`:
  `3164bb9a2c69f4b116d22363861b1cce33f903f45e4421af60f0d3d68e37f8a3`
- `dp_pick_value_context.csv`:
  `c312dd985d78a6edfeeffcba8cf11a56cf729f68ac8eba8c5037b28066184763`
- `dp_playerid_crosswalk_audit.csv`:
  `31178980fd269c660c815cfbeadc214177252742e4fb3df00e5adeae03c754e2`

Result: `PASS_5_OF_5_UNCHANGED`.

Persistent root `%LOCALAPPDATA%\NinersWarRoom\data` remains 14 files,
542,801 bytes, Digest V1
`88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`.

Recovery root `%LOCALAPPDATA%\NinersWarRoom\recovery\data-health` remains 7
files, 172,878 bytes, Digest V1
`1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.

All mutation tests used synthetic temporary directories. No persistent,
recovery, or live opaque restoration is required.
