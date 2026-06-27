# Trade Targets Spec - R&D Only

Purpose: future buy/sell/watch-list support without turning market data into NWR trade valuation.

Safe output now: roadmap/status only.

Blocked output: buy/sell target, trade package recommendation, target score.

Required data: league rosters, manager context, NWR rank context, roster needs, market sanity context, injury/status, and user strategy.

Proposed mechanics: rank context plus roster need plus age/tier fit plus display-only market sanity. This is not implemented.

Current NWR coverage: Trading Lab supports manual package work and display-only market sanity, not target generation.

Build decision: `BLOCKED_NEEDS_MODEL_GATE`.

Safety notes: DynastyProcess, ADP, and market values remain display-only and cannot drive target lists.

Next step: create a trade-target policy and recommendation gate.

Sources: DynastyProcess data https://github.com/dynastyprocess/data and ffscrapr DynastyProcess reference https://ffscrapr.ffverse.com/reference/dp_values.html.
