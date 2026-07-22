# Primary and persistent-state preservation

The user-owned primary worktree remains unchanged with exactly the same five
modified tracked DynastyProcess CSVs. Only metadata and SHA-256 were read:

- `dp_freshness_report.csv`: `1e4212694f19cce9db75af01b91e3827c6a124cca036e872407076b0d89f6c81`
- `dp_market_baseline_context.csv`: `6a8bb153a8e2e2bb8cdd08c586a34bdfebfbdd6a0ddfe681e4182127495be824`
- `dp_nwr_join_coverage.csv`: `331a47087e784e4ec2392b78fdad6c27db3f8fd26383efa2ef9208756708e1cb`
- `dp_pick_value_context.csv`: `97c6c74abd4d9cf17d6aea4cbbb0495745b8d75440ec0c0b95581e2d78fab7bb`
- `dp_playerid_crosswalk_audit.csv`: `d0f78739e6828408badb5a6b2062a2503e42a68e115946941371d6f89244407f`

Persistent product state remains 14 files / 542,801 bytes. Recovery remains
7 files / 172,878 bytes. Metadata-only Digest V1 values are:

- persistent: `88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`
- recovery: `1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`

All negative-control writes were confined to pytest temporary directories.
Source, rejected-review, stable-runtime, and primary worktrees were not edited.
