# Gate C Inventory - 2026-06-30

## Current Master

- Expected/current base: `291d219a705897bece621ac41bfd779bb3cd1791`
- Worktree branch: `work/historical-rookie-label-source-policy-v1-20260630`

## Current Rookie Gate Artifacts

- Gate A approval artifact: `docs/hq/rookie_outcomes/cfbd_rookie_identity_approval_v1_20260629/cfbd_rookie_identity_human_approval_v1.csv`
- Gate A approved identity rows: 157
- Gate A deferred rows: 56
- Gate B draft-capital artifact: `docs/hq/rookie_outcomes/rookie_draft_capital_review_v1_20260629/rookie_draft_capital_review_artifact_v1.csv`
- Gate B review-only round/pick/team rows: 54
- Gate B rows still missing draft capital: 103
- Prior Gate C blocker: `docs/hq/rookie_outcomes/rookie_historical_labels_v1_20260629/`

## CFBD / Identity Inputs

- CFBD review artifacts are review-only and remain `model_use_allowed=false`.
- CFBD identity matching V1 remains review-only.
- Gate-A approval is identity-review-only, not model/training/source-truth approval.
- Current approved CFBD rows do not contain a GSIS/NFL outcome `player_id` bridge.

## Outcome V2 5Y Branch

- Branch inspected: `origin/work/outcome-v2-5y-data-coverage-20260630`
- Branch HEAD: `e9cef8d2456164c93151d5e841de46010efd9d8e`
- Branch was not merged or cherry-picked in this lane.
- Diff is not directly merge-safe here because it predates latest rookie Gate B work.

## Shared Outcome V2 Outputs

- Shared output root inspected: `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended`
- Outputs present: `True`
- Anchor/horizon rows: 7440
- Season rows: 7440
- Complete 5Y rows: 1064
- Seasons: 2012-2024
- Scoring mode: `exact_verified_first_downs`
- Review-only: `yes`

## Source Policy Docs Found

- `docs/hq/data_sources/nfl_usage/NWR_NFL_USAGE_SOURCE_CONTRACT_V0_20260624.md`
- `docs/hq/data_sources/nfl_usage/target_backtest/NWR_NFL_USAGE_HISTORICAL_EXPANSION_STRATEGY_20260624.md`
- `docs/hq/data_sources/nfl_usage/NWR_NFLREADPY_DEPENDENCY_APPROVAL_20260624.md`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/README.md`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/README.md`

## Inventory Conclusion

The NFL outcome target source is available for review-only target truth,
but current CFBD-approved rookie identities cannot be converted into
historical rookie labels because the draft-class/GSIS bridge is missing.
Bridge rows audited: 157.
