# NWR Batch Canonicalization Next Push Guard

## Required Guarded Push Preconditions

Before any push, run:

```bash
git fetch origin
git rev-parse origin/work/hq-parallel-control
git rev-parse HEAD
git status --short
```

Required remote HEAD:

`a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc`

Required local state:

- local HEAD is the combined batch canonicalization commit
- worktree is clean
- local branch is ahead of `origin/work/hq-parallel-control` by exactly `1`
- changed paths are limited to docs/review artifact paths included in the batch
- no app/runtime paths changed
- no ranking/model scoring paths changed
- no source-gate code changed
- no canonical board artifacts changed
- no `local_exports` handling changed
- no production/model-use/source promotion language introduced

## Push Method

Only non-force push is allowed.

Do not push if remote moved. If remote moved, stop and return the new remote HEAD for Master HQ review.

## Post-Push Checks

After push, verify:

- `origin/work/hq-parallel-control` points to the combined batch commit
- changed paths remain limited to the batch docs paths
- no production/source/ranking/app/model/formula behavior changed

## Expected Next Lane

`guarded batch push`
