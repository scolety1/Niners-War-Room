# Primary and Persistent State Preservation

## Opaque primary files

- `dp_freshness_report.csv`: SHA-256 `1e4212694f19cce9db75af01b91e3827c6a124cca036e872407076b0d89f6c81` — hash-only pass.
- `dp_market_baseline_context.csv`: SHA-256 `6a8bb153a8e2e2bb8cdd08c586a34bdfebfbdd6a0ddfe681e4182127495be824` — hash-only pass.
- `dp_nwr_join_coverage.csv`: SHA-256 `331a47087e784e4ec2392b78fdad6c27db3f8fd26383efa2ef9208756708e1cb` — hash-only pass.
- `dp_pick_value_context.csv`: SHA-256 `97c6c74abd4d9cf17d6aea4cbbb0495745b8d75440ec0c0b95581e2d78fab7bb` — hash-only pass.
- `dp_playerid_crosswalk_audit.csv`: SHA-256 `d0f78739e6828408badb5a6b2062a2503e42a68e115946941371d6f89244407f` — hash-only pass.

No opaque contents were read or transformed.

## Persistent and recovery state

- Persistent: 14 files / 542,801 bytes / Digest V1 `88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`.
- Recovery: 7 files / 172,878 bytes / Digest V1 `1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.
- Retained backups: five directories / 15 files.
- Recovery snapshot: one `data-health` recovery directory / seven files.

These values were checked at lane start and are rechecked at each major gate.
