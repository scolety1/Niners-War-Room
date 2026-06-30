# Manual Review Intake 2026-06-30

This folder is an intake and planning package for converting live human review observations into structured model-upgrade evidence.

It is evidence-only. It does not change rankings, tiers, Dynasty Rank, Final Board Rank, model logic, source-truth gates, app behavior, draft runtime behavior, or production outputs.

## Base

- Branch: `work/manual-review-model-upgrade-intake-v0-20260630`
- Worktree: `C:\NWR\Niners-War-Room-manual-review-model-upgrade-intake-v0-20260630`
- Base remote checked after fetch: `origin/work/hq-parallel-control`
- Actual base HEAD: `18ecf909103439aad4077aafd798107bebe7bc64`

## Files

- `MANUAL_REVIEW_INTAKE_STATUS.md`: executive summary and next-lane recommendations.
- `manual_review_issue_matrix.csv`: primary issue intake matrix with conservative flags.
- `model_upgrade_candidate_matrix.csv`: model feature and target candidates only.
- `source_gate_needed_matrix.csv`: source, identity, and policy gates needed before use.
- `blocked_do_not_use_matrix.csv`: hard-blocked items that must not become model/rank inputs.
- `app_ux_patch_candidate_matrix.csv`: safe display and UX candidates.
- `manual_review_taxonomy.md`: classification and action definitions.

## Inventory Scope

Evidence was inventoried from tracked repo artifacts and ignored-worktree checks. The ignored export folder was absent in this isolated worktree, and no raw local export, shared-data, cache, API, vendor, Gmail, or secret file was added.

Primary repo areas reviewed:

- `docs/hq/review_queue/morning_review_20260626/`
- `docs/hq/app_ux/`
- `docs/hq/outcomes/`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/`
- `docs/hq/data_sources/nfl_usage/`
- `docs/hq/future_tools/`
- `docs/hq/rookie_outcomes/`
- `docs/hq/rookie_model/`
- `docs/draft_day_exports/final_board_v1_20260622/app_props/`
- `docs/model_v4/`

## Guardrail Summary

All issue rows default to:

- `rank_change_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`

Display-only context stays display-only. Source-gate-needed rows require a named gate. Blocked rows cannot enable model use.
