# Weekly Lineup Findings

No production Desktop weekly lineup/start-sit optimizer was found. The candidate has roster state and league scoring, which are prerequisites, not a completed workflow. The deeply inspected `evanng07` repository does not solve this; it primarily displays projections.

## Build

Implement a deterministic legal-slot optimizer over the exact Sleeper roster and league positions. Use governed weekly projection snapshots and expose:

- optimal starters and bench;
- legal-slot reasoning and flex alternatives;
- projected margin between choices;
- floor/ceiling and confidence when actually sourced;
- injury, inactive, bye and freshness flags;
- `close call` when evidence does not justify certainty;
- before/after comparison for waiver adds.

The optimizer must remain useful offline from the last fresh snapshot, refuse illegal lineups, and never write to Sleeper. Weather/odds/news are optional evidence lanes, not hidden score modifiers. Backtest weekly projection/decision accuracy before strong claims.
