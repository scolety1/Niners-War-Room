# NWR Master Source Trace

## Canonical Sources Read

- `origin/work/hq-parallel-control` at `a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc`
- `docs/hq/deep_research_upgrades/orchestration_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_feature_discovery_registry_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_public_source_status_reconciliation_v2_20260708/`
- `docs/hq/deep_research_upgrades/hq1_candidate_metric_formula_cards_v21_20260708/`
- `docs/hq/deep_research_upgrades/hq1_route_yprr_tprr_source_admission_search_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_closeout_adoption_map_v1_20260708/`
- `docs/hq/model/formula_gauntlet_revival_lane_setup_v0_20260708/`
- `docs/hq/model/pfr_rb_broken_tackle_formula_gauntlet_design_v1_20260709/`
- `docs/hq/data_sources/pfr_rb_broken_tackle_review_feature_readiness_v1_20260708/`
- `docs/hq/historical_fantasy_data/route_source_recovery_final_closeout_v1_20260709/`
- `docs/hq/historical_fantasy_data/routes_run_denominator_recovery_v2b_20260709/`
- `docs/hq/historical_fantasy_data/sumer_espn_routes_run_hardening_v1_20260709/`
- `docs/hq/historical_fantasy_data/provider_permission_route_feed_request_v1_20260709/`
- `docs/hq/historical_fantasy_data/provider_outreach_route_feed_response_review_v1_20260709/`
- `docs/hq/historical_fantasy_data/provider_outreach_send_authorization_response_intake_v1_20260709/`
- `docs/hq/data_sources/nwr_2024_2025_nflverse_source_admission_decision_v1_20260708/`

## Local Sources Read

- `C:\NWR\Niners-War-Room-formula-gauntlet-data-readiness-gate-v1-20260708`
- `C:\NWR\Niners-War-Room-formula-gauntlet-no-code-tournament-design-scaffold-v1-20260708`
- `C:\NWR\Niners-War-Room-data-hygiene-historical-label-identity-source-gate-closure-v1-20260708`
- `C:\NWR\Niners-War-Room-data-hygiene-charter-second-advance-merge-review-v1-20260708`
- `C:\NWR\Niners-War-Room-model-v4-historical-receipt-gap-plan-merge-review-v1-20260708`
- `C:\NWR\Niners-War-Room-model-v4-partial-historical-replay-benchmark-v1-20260708`
- `C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708`
- `C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708`
- `C:\NWR\Niners-War-Room-model-v4-app-visible-label-correction-v1-20260708`
- `C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708`
- `C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708`
- `C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708`
- `C:\NWR\Niners-War-Room-model-v4-production-active-human-review-packet-v1-20260708`

## Commands Used For Trace

- `git fetch origin`
- `git rev-parse origin/work/hq-parallel-control`
- `git log --oneline -20 --decorate`
- `rg --files docs/hq`
- `Select-String` over route, PFR, Formula Gauntlet, Model v4, and Data Hygiene reports
- `Import-Csv` row count checks for source CSVs

## Trace Caveat

This audit does not inspect every historical file in the repository line by line. It inventories the major recent governance, Model v4, Data Hygiene, Formula Gauntlet, Route Recovery, PFR RB broken-tackle, and benchmark packets relevant to the consolidation decision.
