# Primary-worktree RC2 baseline preservation

This is preservation evidence only and does not approve the CSV contents as canonical data. The five files were hash-checked without inspecting, normalizing, restoring, copying, staging, or committing them.

| File | Required and observed SHA-256 |
| --- | --- |
| `dp_freshness_report.csv` | `1e4212694f19cce9db75af01b91e3827c6a124cca036e872407076b0d89f6c81` |
| `dp_market_baseline_context.csv` | `6a8bb153a8e2e2bb8cdd08c586a34bdfebfbdd6a0ddfe681e4182127495be824` |
| `dp_nwr_join_coverage.csv` | `331a47087e784e4ec2392b78fdad6c27db3f8fd26383efa2ef9208756708e1cb` |
| `dp_pick_value_context.csv` | `97c6c74abd4d9cf17d6aea4cbbb0495745b8d75440ec0c0b95581e2d78fab7bb` |
| `dp_playerid_crosswalk_audit.csv` | `d0f78739e6828408badb5a6b2062a2503e42a68e115946941371d6f89244407f` |

All five hashes matched after the classifier correction, after Hermetic validation, and after the pre-commit runtime cycles. Immediate pre-commit and post-commit checks are mandatory release gates.
