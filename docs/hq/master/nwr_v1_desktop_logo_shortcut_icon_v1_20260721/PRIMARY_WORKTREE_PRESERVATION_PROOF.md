# Primary worktree preservation proof

Only path, SHA-256, byte size, and filesystem timestamps were read. Contents were not inspected, parsed, normalized, restored, copied, staged, committed, or pushed.

| Repository-relative path | SHA-256 | Bytes | Modified UTC |
|---|---|---:|---|
| `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_freshness_report.csv` | `1e4212694f19cce9db75af01b91e3827c6a124cca036e872407076b0d89f6c81` | 790 | 2026-07-18T14:00:12.3470958Z |
| `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_market_baseline_context.csv` | `6a8bb153a8e2e2bb8cdd08c586a34bdfebfbdd6a0ddfe681e4182127495be824` | 215064 | 2026-07-18T14:00:12.3120948Z |
| `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_nwr_join_coverage.csv` | `331a47087e784e4ec2392b78fdad6c27db3f8fd26383efa2ef9208756708e1cb` | 3054 | 2026-07-18T14:00:12.3460972Z |
| `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_pick_value_context.csv` | `97c6c74abd4d9cf17d6aea4cbbb0495745b8d75440ec0c0b95581e2d78fab7bb` | 38099 | 2026-07-18T14:00:12.3210988Z |
| `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_playerid_crosswalk_audit.csv` | `d0f78739e6828408badb5a6b2062a2503e42a68e115946941371d6f89244407f` | 191037 | 2026-07-18T14:00:12.3260971Z |

All five remained exact after asset creation, disposable shortcut testing, Hermetic validation, and the pre-documentation checkpoint.
