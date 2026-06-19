# Trading Lab Fantasy Trade Package Schema

Date: 2026-06-18

## Purpose

This schema defines a manual fantasy trade package contract for future T21 UI
work. It does not add UI, app wiring, source integration, or data ingestion.

## Required Fields

- `trade_mode`: `trade_for`, `trade_away`, or `package_builder`
- `target_player`: player we want to acquire, if applicable
- `outgoing_player`: player we want to move, if applicable
- `give_assets`: players or picks we would give
- `get_assets`: players or picks we would receive
- `picks_included`: rookie or future picks included in the package
- `nwr_value_delta`: private NWR value gain/loss for our roster
- `public_market_fairness`: public fantasy market value comparison
- `opponent_fit_score`: estimate of whether the partner could accept
- `roster_impact_score`: effect on our lineup/depth
- `keeper_impact`: keeper-slot effect
- `drop_pressure_impact`: Drop Decision pressure effect
- `rookie_pick_context`: Rookie/Mock Draft context
- `negotiation_ladder`: opening, fair, max, and walk-away lines
- `risk_flags`: risks such as injury, bye, age, role, or roster imbalance
- `verdict`: manual recommendation label for review
- `review_status`: draft, needs review, ready for manual review, or rejected

## Notes

The schema supports fantasy trade scenario testing only. It must not submit
offers, automate acceptance, ingest data, fetch sources, or change roster state.
