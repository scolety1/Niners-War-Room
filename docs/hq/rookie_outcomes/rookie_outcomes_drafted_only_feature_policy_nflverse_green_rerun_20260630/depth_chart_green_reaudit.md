# Depth Chart Green Re-Audit

Approved populated tracked depth-chart receipt now exists in the NFLVerse player-context packet.

## Receipt Facts

- Source artifact: `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md`.
- Dataset row count in build report: `591527`.
- Coverage in build report: `seasons=2024; weeks=22`.
- Current player-context rows with depth-chart position: `192`.
- Current player-context rows with explicit depth rank: `47`.
- Current player-context rows with `depth_team=1` role text: `148`.
- Teams represented in current display joins: `ARI,ATL,BAL,BUF,CAR,CHI,CIN,CLE,DAL,DEN,DET,GB,HOU,IND,JAX,KC,LA,LAC,LV,MIA,MIN,NE,NO,NYG,NYJ,PHI,PIT,SEA,SF,TB,TEN,WAS`.
- Depth-chart positions represented in current display joins: `K,KOR,KR,PR,QB,RB,TE,WR`.
- Player IDs present for display joins: yes, through `nflverse_gsis_id` and `nflverse_sleeper_id` after identity filter.
- Current-only vs historical: current player-context artifact uses 2024 depth-chart receipts; historical point-in-time pre-draft snapshots are not established.

## Policy Result

Depth charts may support a review-only current opportunity watchlist after identity review. They are not historical model features, not pre-draft features without an as-of/leakage gate, and not UDFA confirmation evidence. Missing depth chart data is not no-role.

The prior zero-row conclusion is superseded for current review-only opportunity context. It is not superseded for model/training/historical pre-draft use.

RotoWire, local_exports, and vendor depth-chart sources remain blocked.
