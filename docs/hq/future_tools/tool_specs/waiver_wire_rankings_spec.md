# Waiver Wire Rankings Spec - R&D Only

Purpose: future free-agent prioritization by roster fit and source-approved opportunity context.

Safe output now: roadmap/status only.

Blocked output: waiver ranking, FAAB bid, add/drop recommendation.

Required data: current free-agent pool, roster state, waiver settings, FAAB/priority, injuries/status, usage/opportunity data, and scoring.

Proposed mechanics: availability plus opportunity trend plus roster need plus schedule window. This is not implemented.

Current NWR coverage: Sleeper can support league/free-agent context in principle, but no automated waiver recommendation framework is approved.

Build decision: `BLOCKED_NEEDS_DATA`.

Safety notes: current status gaps cannot be treated as clean availability.

Next step: approve current free-agent source and waiver-specific gate.

Sources: Sleeper API docs https://docs.sleeper.com/ and nflreadr play-by-play docs https://rdrr.io/cran/nflreadr/man/load_pbp.html.
