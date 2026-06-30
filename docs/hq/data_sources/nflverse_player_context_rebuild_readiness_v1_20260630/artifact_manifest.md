# NFLVerse Player Context Rebuild Readiness V1 Manifest

Generated: 2026-06-30

Verdict: `YELLOW_WAITING_FOR_BINDING_ARTIFACT`

## Purpose

This packet prepares a safe rebuild/apply plan for the compact NFLVerse player-context display artifact after approved identity rows receive stable NWR player ID bindings.

This lane does not rebuild `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`.

## Required Binding Before Rebuild

The exact required binding packet is:

`docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/`

The exact required primary binding CSV is:

`docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_v1.csv`

The binding packet must be merged into `origin/work/hq-parallel-control` and must explicitly permit the rebuild with `rebuild_player_context_permitted=true` in its manifest or guardrail report.

Binding artifact exists in this HQ base: `false`

## Inputs Reviewed

- `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/`
- `docs/hq/data_sources/nflverse_schedule_context_display_gate_v1_20260630/`
- `docs/hq/data_sources/nflverse_display_upgrade_closeout_20260630/`

## Outputs

- `artifact_manifest.md`
- `rebuild_readiness_summary.md`
- `required_binding_contract.md`
- `player_context_rebuild_plan.md`
- `expected_artifact_delta_matrix.csv`
- `rebuild_guardrail_test_plan.md`
- `app_consumption_after_rebuild_plan.md`
- `merge_safety_report.md`

## Scope

Docs/CSV readiness packet only.

No app pages, model logic, rank logic, source-truth files, protected artifacts, latest pointers, runtime JSON, raw shared cache, local exports, vendor paths, or secrets are changed.
