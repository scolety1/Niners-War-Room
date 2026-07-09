# PFR RB Broken Tackle Addendum Source Trace

## Current Remote And Prior Audit

- Current remote HQ verified: `a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc`
- Prior full system audit commit verified locally: `6bc013bea5925525ed8326cc62ca97c1d0ca5ab2`
- Prior full system audit artifact path: `C:\NWR\Niners-War-Room-full-system-audit-integration-map-v1-20260709\docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709`

## Canonical Packets Read

- `docs/hq/data_sources/pfr_rb_broken_tackle_review_feature_readiness_v1_20260708/PFR_RB_BROKEN_TACKLE_REVIEW_FEATURE_READINESS_V1_REPORT.md`
- `docs/hq/data_sources/pfr_rb_broken_tackle_review_feature_readiness_v1_20260708/PFR_RB_BROKEN_TACKLE_REVIEW_FEATURE_READINESS_V1_USE_GATE.md`
- `docs/hq/data_sources/pfr_rb_broken_tackle_review_feature_readiness_v1_20260708/pfr_rb_bt_readiness_signal_summary.csv`
- `docs/hq/data_sources/pfr_rb_broken_tackle_review_feature_readiness_v1_20260708/pfr_rb_bt_readiness_variant_gate.csv`
- `docs/hq/data_sources/pfr_rb_broken_tackle_review_feature_readiness_v1_20260708/pfr_rb_bt_readiness_evidence_manifest.csv`
- `docs/hq/model/pfr_rb_broken_tackle_formula_gauntlet_design_v1_20260709/PFR_RB_BROKEN_TACKLE_FORMULA_GAUNTLET_DESIGN_V1_REPORT.md`
- `docs/hq/model/pfr_rb_broken_tackle_formula_gauntlet_design_v1_20260709/PFR_RB_BROKEN_TACKLE_FORMULA_GAUNTLET_DESIGN_V1_USE_GATE.md`
- `docs/hq/model/pfr_rb_broken_tackle_formula_gauntlet_design_v1_20260709/pfr_rb_bt_gauntlet_locked_feature_contract.csv`
- `docs/hq/model/pfr_rb_broken_tackle_formula_gauntlet_design_v1_20260709/pfr_rb_bt_gauntlet_design_source_manifest.csv`
- `docs/hq/model/formula_gauntlet_revival_lane_setup_v0_20260708/guardrails.md`
- `docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708/HQ1_RECEIPT_CHAIN_USE_GATE.md`
- `docs/hq/historical_fantasy_data/route_source_recovery_final_closeout_v1_20260709/ROUTE_SOURCE_RECOVERY_FINAL_CLOSEOUT_V1_SUMMARY.md`

## Local Packets Read

- `C:\NWR\Niners-War-Room-full-system-audit-integration-map-v1-20260709\docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709\NWR_FULL_SYSTEM_AUDIT_INTEGRATION_MAP_V1_REPORT.md`
- `C:\NWR\Niners-War-Room-full-system-audit-integration-map-v1-20260709\docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709\NWR_DATA_STAT_INVENTORY.csv`
- `C:\NWR\Niners-War-Room-full-system-audit-integration-map-v1-20260709\docs\hq\master\nwr_full_system_audit_integration_map_v1_20260709\NWR_FORMULA_GAUNTLET_READINESS_AUDIT.md`

## Source Provenance Clarification

The PFR advanced stat source clarified for this addendum is nflverse public PFR advanced stat parquet:

- `advstats_season_pass`
- `advstats_season_rush`
- `advstats_season_rec`

The canonical PFR RB readiness packet references `pfr_advanced_source_provenance_hardening_v1` and the source-provenance commit `a0119877571d0255aa0bee6bbefedad52afd5447`, which hardened the public PFR/nflverse endpoint and recorded the PFR rushing source SHA `28f44be62bd30291d5310ff62a453025d804b4d0b6720da820cb6cd943c45187`.

## Guardrail Confirmation

This addendum did not run Formula Gauntlet, did not tune, did not promote PFR, did not add raw parquet/cache files, did not change rankings, and did not change app/runtime behavior.
