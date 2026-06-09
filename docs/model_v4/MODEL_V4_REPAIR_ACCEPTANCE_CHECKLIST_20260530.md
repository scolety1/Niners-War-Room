# Model v4 Repair Acceptance Checklist

Use this checklist to audit the 2026-05-30 repair run.

## Source Routing

- [ ] `ReviewScoreEnvelope` or equivalent exists and requires source disclosure.
- [ ] Primary Player Board value routes to `checkpoint_review_score`.
- [ ] Cross-asset review surfaces route to admitted Model v4 score columns.
- [ ] Unknown, market-only, and legacy lineages cannot remain primary.

## Legacy Quarantine

- [ ] Legacy active-pack `private_score` is exposed only as `legacy_active_pack_score`.
- [ ] Keenan Allen legacy `82.4` is not primary.
- [ ] Darius Slayton legacy `78.88` is not primary.
- [ ] Darius Slayton fails closed if no current Model v4 row exists.

## Join And Evidence Gates

- [ ] Duplicate joins require manual review.
- [ ] Unmatched joins require manual review.
- [ ] Stale team/status evidence is visible.
- [ ] Missing role evidence is visible.
- [ ] Partial/quarantined contributions are visible.

## Market No-Leakage

- [ ] Market rows are display-only.
- [ ] Market rows do not set primary review score.
- [ ] Market rows do not set primary review label.
- [ ] Market labels avoid buy/sell/target/avoid/pay/trade-for framing.

## Review-Only Language

- [ ] External Asset Reviews language replaces trade target framing.
- [ ] Main UI pages show the review-only banner.
- [ ] UI copy does not create final trade, cut, keep, draft, buy, sell, or target recommendations.
- [ ] Score tables/cards show source, column, version or formula version, lineage, trust/confidence, and warnings where available.

## Rookie Pick Gates

- [ ] Neutral pick labels are only `use_pick_review`, `hold_pick_value_context`, or `manual_decision_required`.
- [ ] `5.04` remains manual/no-exact-baseline in evidence fields.
- [ ] Trade-down/future/current-player comparison modes require concrete comparator rows.
- [ ] Absent trade-down comparators do not emit trade-down comparison mode.

## Cross-Asset Disclosure

- [ ] Startup Slot review rows disclose source path, source column, and lineage.
- [ ] Startup Slot pick-zone rows disclose source path, source column, and lineage.
- [ ] Roster Opportunity Cost rows disclose source path, source column, and lineage.
- [ ] Rookie Pick Decision Lab rows and compare rows disclose source path, source column, and lineage.
- [ ] External Asset Review rows disclose source path, source column, and lineage.

## Required Tests

- [ ] `tests/test_model_v4_final_sentinel_gate.py`
- [ ] `tests/test_review_score_envelope_service.py`
- [ ] `tests/test_player_board_score_service.py`
- [ ] `tests/test_market_gap_service.py`
- [ ] `tests/test_model_v4_rookie_pick_decision_lab_service.py`
- [ ] `tests/test_model_v4_startup_slot_simulator_service.py`
- [ ] `tests/test_model_v4_roster_opportunity_cost_service.py`
- [ ] `tests/test_model_v4_sprint14c_trade_review_service.py`
- [ ] `tests/test_trust_banner_ui.py`
- [ ] `tests/test_model_v4_phase5_clean_display_language.py`
- [ ] `tests/test_navigation_compression.py`

## Final Acceptance Question

Can a future agent begin formula tuning only after preserving these source-routing,
market-isolation, copy, disclosure, and sentinel gates?

Accepted verdict:

- `repair_gate_passed_for_review_only_source_routing`

Blocked verdict:

- `needs_repair_before_formula_tuning`
