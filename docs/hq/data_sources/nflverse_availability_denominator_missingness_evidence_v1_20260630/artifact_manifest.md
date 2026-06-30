# NFLVerse Availability Denominator Missingness Evidence Manifest

- artifact: `nflverse_availability_denominator_missingness_evidence_v1_20260630`
- verdict: `YELLOW_AVAILABILITY_MISSINGNESS_EVIDENCE_READY_HEALTH_INFERENCE_BLOCKED`
- base_head: `a35c2c1c7339d7a745d5d90e8af8d0624155a85c`
- created_scope: data hygiene evidence only
- display_artifact_rebuilt: `false`
- app_behavior_changed: `false`
- model_or_source_truth_changed: `false`

## Inputs

- `docs\hq\data_sources\nflverse_availability_denominator_display_v1_20260630\availability_denominator_display_artifact.csv` sha256 `ce09a8ea5a76833aa88bf748725f16318095ac7688e78b77c9bc7537afd548d3`
- `docs\hq\data_sources\nflverse_availability_denominator_display_v1_20260630\availability_denominator_join_health.csv` sha256 `9430eef7939134d4a4c60f3948b2a4e6c9a2df6ed24de4411474075b5ef68cf7`
- `docs\hq\data_sources\nflverse_availability_denominator_display_v1_20260630\availability_denominator_schema_manifest.csv` sha256 `2e50bbf33cca0bff297a15112b5745d3dbab452930e46c06aefcd9317a2f6d53`
- `docs\hq\outcomes\outcome_rookie_nflverse_feature_policy_gate_v1_20260630\availability_denominator_requirements.md` sha256 `ed0bd72a6d1b5bda87c2028c1f3a8d3c71dc0f72c158c5205af7172f45bc9ebf`
- `docs\hq\outcomes\outcome_rookie_nflverse_feature_policy_gate_v1_20260630\nflverse_feature_gate_matrix.csv` sha256 `2557ef027697101963cfa783a466642870a0ae5ba3db3c1980c469eaa2219f40`
- `docs\hq\injury_availability_context\injury_availability_display_context_safe_upgrade_20260630\UI_COPY_AND_GUARDRAILS.md` sha256 `0b98aff6df20d0b6b4cb99bc105069d8adbb4383661872f7bebc266ef2aec919`
- `docs\hq\data_sources\nflverse_player_context_display_20260630\nflverse_player_context_display_artifact.csv` sha256 `129461e3972d6d378e4a4d00e1fb962ffa37d1a4732ad340af2ba90394c6ad94`
- `docs\hq\data_sources\nflverse_display_update_final_closeout_20260630\final_closeout_status.md` sha256 `d80beeb7c077aa9cd23e0dacce33adcb0844e5c4146264d188453717cd2c83b4`

## Outputs

- `denominator_missingness_summary.md`
- `denominator_field_policy_matrix.csv`
- `missingness_and_censoring_rules.md`
- `games_missed_blocker_report.md`
- `availability_model_risk_report.md`
- `next_gate_recommendations.md`
- `merge_safety_report.md`
