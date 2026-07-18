# Primary Worktree Preservation Proof

Primary worktree: C:\NWR\Niners-War-Room

Before fetch/worktree creation, Git reported exactly five modified files under the DynastyProcess market-baseline packet. Their SHA-256 values matched the user-provided preservation values:

| File | Required SHA-256 | Initial result |
| --- | --- | --- |
| dp_freshness_report.csv | 82a8d8e76145b34cd4b62db9a504dedce2695a7bf20d100b58e09aebd5e994d2 | MATCH |
| dp_market_baseline_context.csv | 36d48732d70d0c4063a8045aa16fd31f524ce1cde524c0c790a35b66e07f97a9 | MATCH |
| dp_nwr_join_coverage.csv | 530f8f78203d038b66c2c79e631db3e91e7b15ca4c7a7a148424cec4991dbd2d | MATCH |
| dp_pick_value_context.csv | 6c3b86b4cc79b017f6cef7ae6238edb7711bce19242397a8cf52deb77f2670de | MATCH |
| dp_playerid_crosswalk_audit.csv | e4445a94fb6a0b602f7524388cea271602cebc90ffb61ae3b31602ec901f13cd | MATCH |

No file content was inspected, normalized, restored, staged, or committed. The isolated worktree contains no copy of these modifications.

Final pre-commit validation repeated all five hashes with zero mismatches. The primary status still contained exactly those five modifications and no other path. The post-commit handoff check must repeat the same proof.
