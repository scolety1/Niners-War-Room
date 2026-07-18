# Primary Worktree Preservation Proof

The primary worktree retained exactly five user-owned modified DynastyProcess CSV files. Only status metadata and SHA-256 hashes were read; file contents were not inspected. None of these paths appears in the implementation or canonicalization diff.

- dp_freshness_report.csv: 82a8d8e76145b34cd4b62db9a504dedce2695a7bf20d100b58e09aebd5e994d2
- dp_market_baseline_context.csv: 36d48732d70d0c4063a8045aa16fd31f524ce1cde524c0c790a35b66e07f97a9
- dp_nwr_join_coverage.csv: 530f8f78203d038b66c2c79e631db3e91e7b15ca4c7a7a148424cec4991dbd2d
- dp_pick_value_context.csv: 6c3b86b4cc79b017f6cef7ae6238edb7711bce19242397a8cf52deb77f2670de
- dp_playerid_crosswalk_audit.csv: e4445a94fb6a0b602f7524388cea271602cebc90ffb61ae3b31602ec901f13cd

Hash-only checks at preflight, implementation validation, review, and canonicalization preparation matched these values. The primary worktree was never used for staging or committing this lane.
