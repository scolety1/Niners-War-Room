# In-Season Rankings Spec - R&D Only

Purpose: future rest-of-season or dynasty-adjusted movement view.

Safe output now: roadmap/status only.

Blocked output: in-season rank, rest-of-season rank, rank movement recommendation.

Required data: weekly production, usage, injuries/status, team/depth context, schedule, and a validated in-season model.

Proposed mechanics: prior dynasty value plus source-approved usage trend plus availability and rest-of-season forecast. This is not implemented.

Current NWR coverage: NFL usage evidence exists as review-only; dynasty rankings remain the current product view.

Build decision: `BLOCKED_NEEDS_MODEL_GATE`.

Safety notes: NFL usage, market, or Outcome context cannot become hidden sort/model input.

Next step: create an in-season model gate and backtest plan.

Sources: nflreadpy https://github.com/nflverse/nflreadpy and nflreadr play-by-play docs https://rdrr.io/cran/nflreadr/man/load_pbp.html.
