# Ingredient Upgrade Canonicalization Diff Scope

## Allowed Scope Used

This local canonicalization commit is limited to:

- `docs/hq/data_hygiene/...`
- `docs/hq/model/...`
- `docs/hq/master/...`

The canonicalization adds accepted review-only packets and the batch canonicalization summary packet.

## Blocked Scope Not Touched

- app/runtime paths
- rankings production code
- model production code
- source promotion registries
- canonical `local_exports`
- current-board artifacts
- hidden sort or recommendation logic
- production configs

## Validation Intent

Before local commit, run:

- CSV parse for newly canonicalized CSVs where feasible
- required artifact existence check
- protected-path scan
- staged path scope check
- `git diff --check`
- `git diff --cached --check`
- worktree clean after commit
