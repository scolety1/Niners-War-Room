# NFLVerse Player Stats Row-Level Source Admission V1 Manifest

- artifact: `nflverse_player_stats_row_level_source_admission_v1_20260630`
- verdict: `GREEN_PLAYER_STATS_ROW_LEVEL_SOURCE_ADMITTED_REVIEW_ONLY`
- base_head: `acba9fabf7320dbb89213b074bebe8948e6aca25`
- approved_runner_used: `true`
- runner_snapshot_label: `player_stats_source_admission_v1_20260630`
- runner_created_at: `2026-07-01T01:35:45.256663+00:00`
- local_snapshot_root: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630`
- raw_rows_tracked_in_git: `false`
- review_receipt_tracked_in_git: `true`
- label_truth_allowed: `false`
- model_use_allowed: `false`
- training_allowed: `false`
- source_truth_allowed: `false`

## Inputs

- `docs\hq\outcomes\nflverse_player_stats_sidecar_builder_v1_20260630\player_stats_sidecar_build_summary.md` sha256 `6ce71cb12cf83cb84b8d438be4e0e1acbda99bc04c1552886781c705d0ccac4e`
- `docs\hq\outcomes\nflverse_player_stats_sidecar_builder_v1_20260630\blocked_sidecar_build_report.md` sha256 `e800d859301f3bc0ed073630147523b7f1779684677279acb1bff8511db8111f`
- `docs\hq\outcomes\nflverse_player_stats_sidecar_builder_v1_20260630\player_stats_sidecar_coverage_matrix.csv` sha256 `0551df15005660d077b1f8542b4e536647a394c9386ddd82619b3c8af392dc43`
- `docs\hq\outcomes\nflverse_experiment_substrate_build_plan_v1_20260630\player_stats_sidecar_contract.md` sha256 `196913ba2efbbbdd71f0d84107ae5ac49413cb1dfb50432278f17151632bdd23`
- `docs\hq\outcomes\nflverse_experiment_substrate_build_plan_v1_20260630\allowed_source_inputs.csv` sha256 `dc6fc5617bc4cd2a9294fd890697fc1a5aaa2dd213277c23db496faba738b375`
- `docs\hq\outcomes\nflverse_player_stats_sidecar_overlap_v1_20260630\player_stats_sidecar_overlap_matrix.csv` sha256 `6ccdd99547757c0f7fd34280140c673c865d3b47cab5cc9d6cc823c1843855b4`
- `docs\hq\outcomes\nflverse_label_parity_outcome_sidecar_evidence_v1_20260630\nflverse_player_stats_sidecar_matrix.csv` sha256 `ef1e19c317389f4bacfee1bc84c6f0dd3ceaec83568cfa79b7e24e1c8e55e581`
- `docs\hq\data_sources\nflverse_dataset_level_refresh_health_20260630\nflverse_dataset_registry_v1.csv` sha256 `86f398e2dfae026db4b91650c944832406cdfde91b466fbc8d2f7994bb1e2624`
- `docs\hq\data_sources\nflverse_dataset_level_refresh_health_20260630\nflverse_dataset_coverage_matrix_v1.csv` sha256 `a6f89522575764f37b49960810b45b6440822a11ceb5bed11fc85e6c1269623f`
- `src\services\nflverse_refresh_health_service.py` sha256 `8f36b35bdf7b2a42a7ba082db342042571830b0da6e89d7722d6bd76de2ebe72`
- `scripts\run_nflverse_refresh_v0.ps1` sha256 `1065ed17a30e97f895f946f2f7ed3d29db614a17701f6eb33b51b4e33e8c848c`
- `scripts\nflverse_scheduled_pull_v0.py` sha256 `e3c08814cf6bf440ceed93716cb294faa91b98fe2b1f49b093e986ac5327fe60`

## Local Runner Metadata

- `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630\snapshot_metadata.json` sha256 `6a135b79a3b9838e66799d9f83d1bdae3093d0239b2290846ad2c09df3c09120`
- weekly raw sha256 `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- seasonal raw sha256 `57f76cfeee3211885f6d05504cc61b6529d023d5eb15a60ae21cc81c21c07b59`

## Outputs

- `source_admission_summary.md`
- `player_stats_source_inventory.csv`
- `player_stats_row_level_receipt.csv`
- `player_stats_schema_manifest.csv`
- `source_policy_guardrail_report.md`
- `sidecar_builder_handoff.md`
- `merge_safety_report.md`
