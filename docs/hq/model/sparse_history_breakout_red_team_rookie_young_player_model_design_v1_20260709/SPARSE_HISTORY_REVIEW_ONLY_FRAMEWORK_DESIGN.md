# Sparse-History Review-Only Framework Design

## Modules

1. `SPARSE_HISTORY_ELIGIBILITY_GATE`
   Identifies player-seasons where PYF or multi-year production is likely under-informed.

2. `ROLE_PROMOTION_SIGNAL`
   Uses lagged snap/depth role score, role archetype, and role usage bucket as review-only breakout diagnostics.

3. `DEPTH_CHART_STARTER_SIGNAL`
   Uses lagged starter/depth-chart rows to identify players whose prior production may understate current opportunity.

4. `SNAP_GROWTH_SIGNAL`
   Uses prior-season snap-share trend and games with offensive snaps as a bounded role-growth signal.

5. `AVAILABILITY_REBOUND_SIGNAL`
   Uses availability context only as a caution/rebound slice, not an injury prediction model.

6. `DRAFT_CAPITAL_CONTEXT`
   Uses positive draft evidence and draft capital buckets as sparse-history context. CFBD/prospect and inferred UDFA truth remain blocked.

7. `AGE_LIFECYCLE_WINDOW`
   Uses age/lifecycle buckets as position-specific context, not automatic boosts or penalties.

8. `EXPECTED_OPPORTUNITY_PARTIAL_WINDOW_SIGNAL`
   Uses ffopportunity/NGS only in partial-window diagnostics unless future coverage expands.

9. `POSITION_SPECIFIC_BREAKOUT_RULES`
   Requires separate QB/RB/WR/TE rule profiles because sparse-history breakouts do not share one universal curve.

10. `FALSE_POSITIVE_TRAP_FLAGS`
    Flags draft-without-role, weak depth, low snap, injury caveat, weak role archetype, and sparse production without promotion.

## Required Rule-Test Guardrails

- Predeclare all rules before testing.
- Keep full-history, broad-window, and partial-window scoreboards separate.
- Do not use current-only ADP, CFBD/prospect data, SportsDataIO, PFF Elusive Rating, or same-season/future context.
- Do not approve production/model-use, rankings integration, hidden sort, or recommendation logic.
