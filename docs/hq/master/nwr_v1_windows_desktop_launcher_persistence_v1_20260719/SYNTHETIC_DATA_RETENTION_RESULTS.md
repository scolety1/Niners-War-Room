# Synthetic data retention results

- Empty isolated profile initialized without inventing a draft.
- Synthetic mock runtime was written and loaded through `draft_day_runtime_state_service` outside the worktree.
- Clean start/readiness/stop/restart passed; exact state hash was retained.
- Duplicate launch exited 0 and did not create a second Streamlit process.
- Changing synthetic state during a healthy run created one `post_clean_shutdown` snapshot.
- Backup/restore round trip restored the earlier note through the owning draft service.
- Restore dry-run reported replacement before mutation.
- A tampered snapshot was rejected.
- An interrupted temporary file did not replace the valid atomic state.
- Abrupt supervisor/server loss left a stale lock; restart reclaimed only the stale lock, became healthy, preserved the state hash, and cleaned lock/port on stop.
- A replacement repository path using the same data root loaded the same state.
- Initial combined focused result: 75 passed. Post-review ownership/restore regression result: 20 passed, including maintenance-lock exclusion, oldest-at-retention restore, exact absent-file removal, empty-state rollback, readiness error surfacing, visible/logged backup-warning behavior, and warning delivery when its log write also fails.

No real user state was used or mutated.
