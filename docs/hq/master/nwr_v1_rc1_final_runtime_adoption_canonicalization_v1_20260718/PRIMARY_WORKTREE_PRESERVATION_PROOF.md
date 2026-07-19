# Primary worktree preservation proof

The five user-owned DynastyProcess CSVs were treated as preservation-only. Their contents were not inspected, normalized, restored, staged, committed, copied, or pushed. Only explicit read-only SHA-256 checks were performed.

| File | Approved SHA-256 | Before review | After Hermetic | After runtime cycles | Immediately before push | After push |
| --- | --- | --- | --- | --- | --- | --- |
| `dp_freshness_report.csv` | `1e4212694f19cce9db75af01b91e3827c6a124cca036e872407076b0d89f6c81` | match | match | match | match | required final readback |
| `dp_market_baseline_context.csv` | `6a8bb153a8e2e2bb8cdd08c586a34bdfebfbdd6a0ddfe681e4182127495be824` | match | match | match | match | required final readback |
| `dp_nwr_join_coverage.csv` | `331a47087e784e4ec2392b78fdad6c27db3f8fd26383efa2ef9208756708e1cb` | match | match | match | match | required final readback |
| `dp_pick_value_context.csv` | `97c6c74abd4d9cf17d6aea4cbbb0495745b8d75440ec0c0b95581e2d78fab7bb` | match | match | match | match | required final readback |
| `dp_playerid_crosswalk_audit.csv` | `d0f78739e6828408badb5a6b2062a2503e42a68e115946941371d6f89244407f` | match | match | match | match | required final readback |

The primary worktree retained exactly those five pre-existing modifications. No adoption path was staged there. The final operator must record the post-push read-only comparison outside this immutable commit; a mismatch invalidates acceptance.
