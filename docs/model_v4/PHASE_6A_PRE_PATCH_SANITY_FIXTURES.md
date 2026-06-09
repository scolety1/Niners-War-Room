# Phase 6A Pre-Patch Sanity Fixture Snapshot

This report captures the pre-patch Model v4 review-only preview outputs against the sanity fixture contract. Fixture failures are review findings, not automatic formula changes or decision-ready blockers.

## Summary

- Review status: review_only
- Fixtures: 29
- Ready: 23
- Review: 6
- Blocked: 0
- Decision-ready unlocked: False
- Auto-fixes applied: False

## Review Findings

| Fixture | Status | Classification | Actual behavior | Next action |
| --- | --- | --- | --- | --- |
| rb_bijan_rb1_002 | review | formula issue | Bijan Robinson=76.58 (overall 2, RB2, usable); Bijan is RB2, not RB1. | Do not tune blindly; inspect component weights and named receipts. |
| wr_elite_tier_001 | review | data gap | Jaxon Smith-Njigba=50.76 (overall 31, WR9, usable); Puka Nacua=47.64 (overall 37, WR14, usable); Ja'Marr Chase=67.08 (overall 9, WR1, usable); Justin Jefferson=56.63 (overall 23, WR4, usable); Amon-Ra St. Brown=57.93 (overall 19, WR3, usable); CeeDee Lamb=50.51 (overall 32, WR10, usable); Malik Nabers=52.84 (overall 27, WR7, usable); Puka Nacua is below core-tier threshold or has weak confidence. | Inspect source coverage and receipts before changing formulas. |
| wr_puka_core_004 | review | data gap | Puka Nacua=47.64 (overall 37, WR14, usable); Puka Nacua is below core-tier threshold or has weak confidence. | Inspect source coverage and receipts before changing formulas. |
| qb_1qb_suppression_001 | review | formula issue | Josh Allen=59.34 (overall 17, QB3, usable); Jalen Hurts=73.81 (overall 4, QB1, review); Patrick Mahomes=57.51 (overall 20, QB5, review); Jayden Daniels=47.46 (overall 38, QB7, review); Joe Burrow=63.95 (overall 10, QB2, review); Brock Purdy=57.94 (overall 18, QB4, review); Daniel Jones=38.09 (overall 50, QB8, usable); Replaceable QB equals/exceeds elite RB/WR benchmark. | Do not tune blindly; inspect component weights and named receipts. |
| qb_replaceable_control_002 | review | formula issue | Daniel Jones=38.09 (overall 50, QB8, usable); Brock Purdy=57.94 (overall 18, QB4, review); Joe Burrow=63.95 (overall 10, QB2, review); Replaceable QB equals/exceeds elite RB/WR benchmark. | Do not tune blindly; inspect component weights and named receipts. |
| te_no_premium_001 | review | formula issue | Brock Bowers=53.13 (overall 26, TE3, review); Trey McBride=63.68 (overall 11, TE1, review); Sam LaPorta=37.59 (overall 52, TE6, review); George Kittle=57.45 (overall 21, TE2, review); Mark Andrews=47.10 (overall 40, TE5, review); Travis Kelce=49.12 (overall 35, TE4, review); T.J. Hockenson=30.26 (overall 62, TE7, usable); Jake Ferguson=29.44 (overall 63, TE8, usable); Brenton Strange=28.32 (overall 66, TE9, usable); Oronde Gadsden II=12.91 (overall 75, TE10, weak); Replaceable/non-elite TE equals/exceeds elite RB/WR benchmark. | Do not tune blindly; inspect component weights and named receipts. |

## All Fixtures

| Fixture | Status | Severity | Classification |
| --- | --- | --- | --- |
| rb_elite_order_001 | ready | high | acceptable model disagreement |
| rb_bijan_rb1_002 | review | high | formula issue |
| rb_gibbs_near_bijan_003 | ready | medium | acceptable model disagreement |
| rb_achane_core_004 | ready | high | acceptable model disagreement |
| rb_cmc_age_visible_005 | ready | medium | acceptable model disagreement |
| rb_jeanty_young_prior_006 | ready | high | acceptable model disagreement |
| wr_elite_tier_001 | review | high | data gap |
| wr_jsn_top_tier_002 | ready | high | acceptable model disagreement |
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
| qb_1qb_suppression_001 | review | high | formula issue |
| qb_replaceable_control_002 | review | medium | formula issue |
| te_no_premium_001 | review | high | formula issue |
| te_elite_exception_002 | ready | medium | acceptable model disagreement |
| market_isolation_001 | ready | high | acceptable model disagreement |
| market_missing_edge_002 | ready | medium | acceptable model disagreement |
| league_rank_context_001 | ready | high | acceptable model disagreement |
| forced_release_pool_001 | ready | high | acceptable model disagreement |
| source_gap_control_001 | ready | medium | acceptable model disagreement |
| route_unavailable_001 | ready | high | acceptable model disagreement |
| incoming_rookie_lane_001 | ready | medium | acceptable model disagreement |
