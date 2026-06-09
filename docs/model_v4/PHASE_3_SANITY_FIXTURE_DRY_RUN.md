# Phase 3 Sanity Fixture Dry Run

This report compares the Model v4 review-only preview outputs against the sanity fixture contract. Fixture failures are review findings, not automatic formula changes or decision-ready blockers.

## Summary

- Review status: review_only
- Fixtures: 29
- Ready: 26
- Review: 3
- Blocked: 0
- Decision-ready unlocked: False
- Auto-fixes applied: False

## Review Findings

| Fixture | Status | Classification | Actual behavior | Next action |
| --- | --- | --- | --- | --- |
| wr_elite_tier_001 | review | data gap | Jaxon Smith-Njigba=49.93 (overall 15, WR6, usable); Puka Nacua=46.57 (overall 18, WR9, usable); Ja'Marr Chase=66.08 (overall 4, WR1, usable); Justin Jefferson=55.65 (overall 10, WR3, usable); Amon-Ra St. Brown=56.86 (overall 8, WR2, usable); CeeDee Lamb=49.64 (overall 16, WR7, usable); Malik Nabers=52.21 (overall 11, WR4, usable); Jaxon Smith-Njigba, Puka Nacua, CeeDee Lamb is below core-tier threshold or has weak confidence. | Inspect source coverage and receipts before changing formulas. |
| wr_jsn_top_tier_002 | review | data gap | Jaxon Smith-Njigba=49.93 (overall 15, WR6, usable); Jaxon Smith-Njigba is below review threshold or has weak confidence. | Inspect source coverage and receipts before changing formulas. |
| wr_puka_core_004 | review | data gap | Puka Nacua=46.57 (overall 18, WR9, usable); Puka Nacua is below core-tier threshold or has weak confidence. | Inspect source coverage and receipts before changing formulas. |

## All Fixtures

| Fixture | Status | Severity | Classification |
| --- | --- | --- | --- |
| rb_elite_order_001 | ready | high | acceptable model disagreement |
| rb_bijan_rb1_002 | ready | high | acceptable model disagreement |
| rb_gibbs_near_bijan_003 | ready | medium | acceptable model disagreement |
| rb_achane_core_004 | ready | high | acceptable model disagreement |
| rb_cmc_age_visible_005 | ready | medium | acceptable model disagreement |
| rb_jeanty_young_prior_006 | ready | high | acceptable model disagreement |
| wr_elite_tier_001 | review | high | data gap |
| wr_jsn_top_tier_002 | review | high | data gap |
| wr_jsn_vs_tee_003 | ready | high | acceptable model disagreement |
| wr_puka_core_004 | review | medium | data gap |
| wr_chase_jefferson_core_005 | ready | medium | acceptable model disagreement |
| wr_lamb_nabers_same_tier_006 | ready | medium | acceptable model disagreement |
| young_btj_luther_001 | ready | high | acceptable model disagreement |
| young_luther_chase_brown_002 | ready | medium | acceptable model disagreement |
| young_kaleb_veterans_003 | ready | high | acceptable model disagreement |
| young_lifecycle_004 | ready | high | acceptable model disagreement |
| age_wr_vs_rb_001 | ready | high | acceptable model disagreement |
| age_veteran_receipts_002 | ready | medium | acceptable model disagreement |
| qb_1qb_suppression_001 | ready | high | acceptable model disagreement |
| qb_replaceable_control_002 | ready | medium | acceptable model disagreement |
| te_no_premium_001 | ready | high | acceptable model disagreement |
| te_elite_exception_002 | ready | medium | acceptable model disagreement |
| market_isolation_001 | ready | high | acceptable model disagreement |
| market_missing_edge_002 | ready | medium | acceptable model disagreement |
| league_rank_context_001 | ready | high | acceptable model disagreement |
| forced_release_pool_001 | ready | high | acceptable model disagreement |
| source_gap_control_001 | ready | medium | acceptable model disagreement |
| route_unavailable_001 | ready | high | acceptable model disagreement |
| incoming_rookie_lane_001 | ready | medium | acceptable model disagreement |
