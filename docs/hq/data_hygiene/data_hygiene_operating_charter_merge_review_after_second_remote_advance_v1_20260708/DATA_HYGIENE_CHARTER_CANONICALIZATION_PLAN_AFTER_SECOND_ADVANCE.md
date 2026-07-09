# Data Hygiene Charter Canonicalization Plan After Second Advance

## Prepared Local Plan

1. Start from current remote HQ head:
   `a2f7c145be35f1099e9ba7553109c001169bd694`
2. Replay the intended Data Hygiene Operating Charter canonicalization commit:
   `3832b0fccab7f16fcb0d0c114f85a3d12d710f68`
3. Add this second-advance merge-review packet under:
   `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_after_second_remote_advance_v1_20260708/`
4. Create one new local docs-only canonicalization commit.
5. Do not push from this lane.

## Expected Changed Paths

- `docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708/`
- `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_v1_20260708/`
- `docs/hq/data_hygiene/data_hygiene_operating_charter_merge_review_after_second_remote_advance_v1_20260708/`

## Do Not Bundle

Do not bundle this push with Formula Gauntlet execution, PFR source promotion, model benchmarking, ranking changes, app/runtime edits, source-gate changes, source-truth updates, route/YPRR/TPRR admission, or unrelated Data Hygiene work.
