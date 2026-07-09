# NWR Batch Canonicalization V2 Next Push Guard

Use this only after Master HQ separately approves a guarded push.

## Required Guard

1. Run `git fetch origin`.
2. Confirm `origin/work/hq-parallel-control` still equals the pre-push expected remote HEAD recorded in the final response for this lane.
3. Confirm local `HEAD` equals the combined local canonicalization commit from this lane.
4. Confirm the worktree is clean.
5. Confirm local branch is ahead by exactly `1` and behind by `0`.
6. Confirm committed paths are under `docs/hq/`.
7. Confirm protected-path scan is clean:
   - no app/runtime changes
   - no ranking changes
   - no model/formula code changes
   - no source-gate changes
   - no canonical board artifact changes
   - no `local_exports` changes
8. Confirm no source promotion and no production/model-use approval.
9. Push without force only:

```bash
git push origin HEAD:work/hq-parallel-control
```

## Stop Conditions

Stop if the remote advanced, if the branch is behind, if any protected path is present, or if any production/source/ranking/app/model/formula behavior change is detected.
