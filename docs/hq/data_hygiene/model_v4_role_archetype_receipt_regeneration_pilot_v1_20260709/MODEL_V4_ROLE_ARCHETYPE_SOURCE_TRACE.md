# Model v4 Role Archetype Source Trace

## Inputs Used

- Partial replay input panel: `docs\hq\model\historical_model_v4_replay_substrate_v1_20260708\MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`
- Regeneration contract: `docs\hq\master\model_v4_historical_receipt_regeneration_contract_planning_v1_20260709`
- Historical receipt master review: `docs\hq\master\model_v4_historical_receipt_master_review_admission_decision_v1_20260709`
- Freeze/schema validation packet: `docs\hq\data_hygiene\model_v4_historical_receipt_freeze_schema_validation_v1_20260709`
- Confidence-cap pilot context: `docs\hq\data_hygiene\model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709`
- Confidence-cap component signal test context: `C:\NWR\Niners-War-Room-model-v4-confidence-cap-component-signal-test-v1-20260709\docs\hq\model\model_v4_confidence_cap_component_signal_test_v1_20260709` at commit `b548776c4343b7bd38cb63f84b51b0334fd8b352`
- HQ1 receipt-chain/use-gate standard: `docs\hq\deep_research_upgrades\hq1_source_receipt_chain_standard_v1_20260708`
- Data Hygiene operating charter: `docs\hq\data_hygiene\data_hygiene_operating_charter_v1_20260708`

## Safety Notes

- Regenerated only `role_archetype_receipts`.
- Used lagged prior-season fields only.
- Did not run exact replay, Formula Gauntlet, tournaments, tuning, source promotion, rankings integration, or production/model-use.