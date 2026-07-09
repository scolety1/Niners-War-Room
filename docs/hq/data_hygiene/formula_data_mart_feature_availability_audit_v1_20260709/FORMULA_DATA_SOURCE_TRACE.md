# Formula Data Source Trace

Canonical remote HEAD verified before build: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

## Sources Used

- `docs\hq\model\historical_model_v4_replay_substrate_v1_20260708\MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`: base player-season panel with labels, PYF, lagged factual components; `review_only_component_signal_tests_only`; SHA256 `22c7aa9ecb8567d0ff795809d075f8f8ac91a3dfe56e7a31f8a328ba99c9b99f`
- `docs\hq\data_hygiene\model_v4_role_archetype_receipt_regeneration_pilot_v1_20260709\MODEL_V4_ROLE_ARCHETYPE_RECEIPTS_REVIEW_ONLY.csv`: role archetype receipts; `review_only_guardrail_context`; SHA256 `968929928a3b6729ad8624df5c03a7de6106aacee263b9c01fddad8e7ca14653`
- `docs\hq\data_hygiene\model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709\MODEL_V4_CONFIDENCE_CAP_RECEIPTS_REVIEW_ONLY.csv`: confidence cap receipts; `review_only_caution_coverage_context`; SHA256 `53225b3314b66af815cc5df7228b285a2330a0f603784c8dbcba98f50b422e6d`
- `docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709\NWR_DATA_STAT_INVENTORY.csv`: full system stat inventory; `governance_reference`; SHA256 `e547c633f1d5119cd75c7d033761d7b0bb04a1fa6998c61ca5373025027364c7`
- `docs\hq\data_hygiene\historical_label_identity_source_gate_closure_v1_20260708\HISTORICAL_LABEL_IDENTITY_SOURCE_GATE_CLOSURE_V1_REPORT.md`: label/identity/source gate closure; `governance_reference`; SHA256 `8b46c51ba8a4dbb0a427c06992f8666d6ea4243f3a2cae27b65d3460a66ad09a`
- `docs\hq\data_hygiene\model_v4_historical_receipt_locator_ledger_v1_20260709\MODEL_V4_HISTORICAL_RECEIPT_LOCATOR_LEDGER_V1_REPORT.md`: historical receipt locator; `governance_reference`; SHA256 `9170941965e90039b6b7224b74534dd2877f2b85a02c143b264a17f6ca6313dd`
- `docs\hq\data_hygiene\model_v4_historical_receipt_freeze_schema_validation_v1_20260709\MODEL_V4_HISTORICAL_RECEIPT_FREEZE_SCHEMA_VALIDATION_V1_REPORT.md`: receipt freeze/schema validation; `governance_reference`; SHA256 `d4a2f09ad0b56a9ef506f7d9c1d887b2db5c5d1c4f33530b5d5ce0a9808e1343`
- `docs\hq\master\model_v4_historical_receipt_master_review_admission_decision_v1_20260709\MODEL_V4_HISTORICAL_RECEIPT_MASTER_REVIEW_ADMISSION_DECISION_V1_REPORT.md`: receipt admission decision; `governance_reference`; SHA256 `04d5662d6ab9870299cb0ed43a86d0b537d65239dabc30826b1194c98d73fc6a`
- `docs\hq\formula_gauntlet\formula_gauntlet_data_readiness_gate_v1_20260708\FORMULA_GAUNTLET_DATA_READINESS_GATE_V1_REPORT.md`: Formula Gauntlet readiness gate; `governance_reference`; SHA256 `9020497be321cd82277f972fcacb26f48b1d515242363909912ec365a8b859f2`
- `docs\hq\formula_gauntlet\formula_gauntlet_no_code_tournament_design_scaffold_v1_20260708\FORMULA_GAUNTLET_NO_CODE_TOURNAMENT_DESIGN_SCAFFOLD_V1_REPORT.md`: Formula Gauntlet no-code scaffold; `governance_reference`; SHA256 `aced42a37ab79f99fa3e016e1dfb7e11ea058a219056ab67b93397a43ac262bd`
- `docs\hq\master\nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709\NWR_SYSTEM_AUDIT_PFR_RB_BROKEN_TACKLE_ADDENDUM_V1_REPORT.md`: PFR RB broken tackle addendum; `governance_reference`; SHA256 `ae56dc924c328ecd121bed543c98f6ee40339d49b76b4e6de0b70d768ad5a44d`

## Join Result

- Review-only data mart rows: `5518`
- Join grain: `player_id + season + position`
- Role archetype joins missing: `0`
- Confidence cap joins missing: `0`

## Guardrails

- No source was promoted.
- No production/model-use approval was introduced.
- No Formula Gauntlet, tournament, tuning, exact replay, ranking integration, or app/runtime/model behavior change occurred.
- No canonical `local_exports` write occurred.
