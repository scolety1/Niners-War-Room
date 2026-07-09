# Data Hygiene Operating Charter Canonicalization Plan

## Prepared Local Plan

1. Start from current remote HQ head:
   `adcc3eb5110d416ca2b3fa758594aa8d09be2fd3`
2. Replay the intended Data Hygiene Operating Charter V1 commit:
   `87ac505cb49d94378bc1f69a918e8dfa55e4823e`
3. Add this merge-review packet under:
   `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_v1_20260708/`
4. Create a new local docs-only canonicalization commit.
5. Do not push from this lane.

## Expected Local Changed Paths

- `docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708/`
- `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_v1_20260708/`

## Required Push Lane

A separate guarded push lane may push the new local commit only if:

- `origin/work/hq-parallel-control` still points to `adcc3eb5110d416ca2b3fa758594aa8d09be2fd3`.
- Local HEAD is the new local canonicalization commit produced by this lane.
- Local branch is ahead of `origin/work/hq-parallel-control` by exactly one commit.
- Worktree is clean.
- Changed paths are limited to the two Data Hygiene paths listed above.
- Changes are docs-only.
- No source promotion, production/model-use approval, ranking change, app/runtime change, model/formula behavior change, or Data Hygiene boundary violation is present.
- Push is non-force only.

## Do Not Bundle

Do not bundle this canonicalization with Formula Gauntlet execution, model benchmarking, source promotion, ranking changes, app/runtime edits, or unrelated provider/route/YPRR work.
