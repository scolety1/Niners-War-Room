# Backup, restore, and recovery drill

NWR was stopped with port 8520 released before maintenance.

- state validation: VALID_STATE, exit 0;
- manual snapshot: 20260722T185226Z__manual;
- manifest files: 2;
- independent hash/size mismatches: 0;
- restore dry-run: true, exit 0;
- plan: two UNCHANGED targets;
- retention limit: 5;
- valid snapshot directories after pruning: 5;
- real-state restore: not run.

Five focused synthetic-state tests exercised exact confirmation, round-trip
restore, oldest-snapshot retention behavior, empty-state rollback, and removal
of an invalid new file before rollback. All five passed. Destructive behavior
was limited to temporary synthetic state.
