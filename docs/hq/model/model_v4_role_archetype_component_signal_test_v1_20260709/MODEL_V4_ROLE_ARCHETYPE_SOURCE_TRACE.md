# Model v4 Role Archetype Component Signal Source Trace

## Inputs Used

- Role-archetype receipts: `C:\NWR\Niners-War-Room-model-v4-role-archetype-receipt-regeneration-pilot-v1-20260709\docs\hq\data_hygiene\model_v4_role_archetype_receipt_regeneration_pilot_v1_20260709\MODEL_V4_ROLE_ARCHETYPE_RECEIPTS_REVIEW_ONLY.csv` at commit `0462aaa4e01f1939afd1b63dc5fe55bdd4db68fc`
- Partial replay label/PYF panel: `docs\hq\model\historical_model_v4_replay_substrate_v1_20260708\MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`
- Confidence-cap signal context: `C:\NWR\Niners-War-Room-model-v4-confidence-cap-component-signal-test-v1-20260709\docs\hq\model\model_v4_confidence_cap_component_signal_test_v1_20260709` at commit `b548776c4343b7bd38cb63f84b51b0334fd8b352`
- Historical label / identity / source-gate closure: `docs\hq\data_hygiene\historical_label_identity_source_gate_closure_v1_20260708`
- Formula Gauntlet readiness gate: `docs\hq\formula_gauntlet\formula_gauntlet_data_readiness_gate_v1_20260708`
- Full system audit: `docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709`
- HQ1 receipt-chain/use-gate standard: `docs\hq\deep_research_upgrades\hq1_source_receipt_chain_standard_v1_20260708`
- Data Hygiene operating charter: `docs\hq\data_hygiene\data_hygiene_operating_charter_v1_20260708`

## Safety Notes

- Used only regenerated `role_archetype_receipts` plus historical labels/PYF baseline.
- Did not combine formulas or optimize weights.
- Did not run Formula Gauntlet or a tournament.
- Did not write canonical `local_exports`.
- Did not change rankings, app/runtime/model behavior, source gates, or production status.

## Join Result

- Joined rows tested: `5518`
- Join keys: `target_season/season`, `feature_season`, `player_id_gsis/player_id`, `position`.
- Missing joins: `0`.