# Primary Worktree Preservation Proof

The five user-owned DynastyProcess CSV files in the primary worktree were used
only for hash-only preservation checks. They were not opened for content
inspection, normalized, restored, staged, committed, or pushed.

| File | Required and final SHA-256 | Match |
|---|---|---:|
| `dp_freshness_report.csv` | `82a8d8e76145b34cd4b62db9a504dedce2695a7bf20d100b58e09aebd5e994d2` | yes |
| `dp_market_baseline_context.csv` | `36d48732d70d0c4063a8045aa16fd31f524ce1cde524c0c790a35b66e07f97a9` | yes |
| `dp_nwr_join_coverage.csv` | `530f8f78203d038b66c2c79e631db3e91e7b15ca4c7a7a148424cec4991dbd2d` | yes |
| `dp_pick_value_context.csv` | `6c3b86b4cc79b017f6cef7ae6238edb7711bce19242397a8cf52deb77f2670de` | yes |
| `dp_playerid_crosswalk_audit.csv` | `e4445a94fb6a0b602f7524388cea271602cebc90ffb61ae3b31602ec901f13cd` | yes |

The values matched before isolated-worktree creation and again after all
bounded adoption gates. Any later mismatch invalidates push authorization.
