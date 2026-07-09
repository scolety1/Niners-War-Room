# Data Hygiene Charter Next Push Guard After Second Advance

## Expected Remote Before Push

`a2f7c145be35f1099e9ba7553109c001169bd694`

## Required Commands

Run from the second-advance canonicalization worktree:

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
- Local HEAD must equal the new canonicalization commit from this lane.
- Ahead/behind count must be `0 1`.
- Worktree must be clean.
- Changed paths must be limited to:
  - `docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708/`
  - `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_v1_20260708/`
  - `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_after_second_remote_advance_v1_20260708/`
- Changes must be docs-only.
- No source promotion, production/model-use approval, ranking change, app/runtime change, model/formula change, Formula Gauntlet execution, source-gate change, source-truth promotion, or Data Hygiene boundary violation may be present.

## Push Command

Only if every guard passes:

```powershell
git push origin HEAD:work/hq-parallel-control
```

Do not force push.

## Stop Conditions

Stop and report if the remote advances, if the branch is not exactly one commit ahead, if any protected path appears, or if any non-doc change is detected.
