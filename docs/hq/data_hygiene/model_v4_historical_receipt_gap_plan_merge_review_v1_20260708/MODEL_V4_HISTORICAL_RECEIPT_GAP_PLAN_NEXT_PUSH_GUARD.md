# Model v4 Historical Receipt Gap Plan Next Push Guard

## Expected Remote Before Push

`a2f7c145be35f1099e9ba7553109c001169bd694`

## Required Commands

Run from the merge-review worktree:

```powershell
git fetch origin
git rev-parse origin/work/hq-parallel-control
git rev-parse HEAD
git status --short
git rev-list --left-right --count origin/work/hq-parallel-control...HEAD
git diff --name-only origin/work/hq-parallel-control..HEAD
git diff --check origin/work/hq-parallel-control..HEAD
```

## Required Results

- Remote target must still equal `a2f7c145be35f1099e9ba7553109c001169bd694`.
- Local HEAD must equal the local canonicalization commit produced by this lane.
- Ahead/behind count must be `0 1`.
- Worktree must be clean.
- Changed paths must be limited to:
  - `docs/hq/data_hygiene/model_v4_historical_receipt_gap_closure_plan_v1_20260708/`
  - `docs/hq/data_hygiene/model_v4_historical_receipt_gap_plan_merge_review_v1_20260708/`
- Changes must be docs-only.
- No source promotion, production/model-use approval, exact Model v4 replay approval, Formula Gauntlet execution, formula tuning, challenger-score replacement, ranking change, app/runtime/model behavior change, source-gate change, recovered local artifact canonicalization, or canonical `local_exports` write may be present.

## Push Command

Only if every guard passes:

```powershell
git push origin HEAD:work/hq-parallel-control
```

Do not force push.

## Stop Conditions

Stop and report if the remote advances, if the branch is not exactly one commit ahead, if any protected path appears, or if any non-doc change is detected.
