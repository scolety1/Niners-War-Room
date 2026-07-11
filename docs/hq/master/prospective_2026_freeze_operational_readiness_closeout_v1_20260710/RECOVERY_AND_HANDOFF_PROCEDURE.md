# Recovery and Handoff Procedure

## Minimum recovery set

The canonical HQ repository, controlling commit, canonical packet, `MANIFEST.json`, `PROSPECTIVE_2026_FREEZE_MANIFEST.json`, `PRE_REGISTRATION_HASH.txt`, `PRE_REGISTRATION_LOCK.md`, `PROSPECTIVE_2026_BASELINE_FREEZE.csv`, `SOURCE_HASH_LEDGER.csv`, and `FUTURE_2026_OUTCOME_EVALUATION_CONTRACT.md`.

## Steps

1. Fetch the canonical repository and resolve commit `e4693f49fa44dba6e75b488d6a560a88ea715b8d`.
2. Read the packet only from its canonical path at that commit.
3. Recalculate all manifest-listed hashes and the two controlling hashes.
4. Recalculate all 924 player-record hashes using the frozen typed field schema.
5. Confirm PYF 342/231, GAUNTLET 342/231, and current board 240/232.
6. Confirm `PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` is absent for the recorded rejected-challenger reason.
7. Resolve repository-held receipt paths relative to the repository root; verify external source receipts against their recorded hashes when available.
8. If a local cache is unavailable, do not rebuild or substitute it. Record the unavailable receipt and recover it only from an authorized immutable backup matching the ledger hash.
9. Before future evaluation, apply the canonical contract plus this pre-outcome operational addendum.

No old experiment worktree, ZIP, untracked file, chat history, or developer memory is required. The commit and freeze timestamp, reinforced by immutable hashes, establish that predictions preceded authorized outcomes.
