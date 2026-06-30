# Drafted-Only Admission Gate Refresh Audit

`draft_picks` is now present as a GREEN review/display receipt in the NFLVerse player-context packet.

Receipt facts from tracked docs:

- `draft_picks` row count: `514`.
- Coverage: `seasons=2024-2025`.
- Player-context draft-capital join rows: `75` clean joins out of `294` current Rankings rows.
- Historical drafted-only audit rows: `1999`.
- Historical drafted rows with any Outcome V2 label linkage: `897`.

The refreshed receipt supports the existing admission policy: positive `draft_picks` evidence is the only drafted-only admission source. Other datasets can enrich identity/status but cannot admit a player into the drafted-only path.

Round/pick/team completeness is preserved in the historical drafted audit for review purposes. Age, combine, and ff_playerids row-level coverage are not recalculated for all historical rows in this packet because raw refreshed rows are not tracked here and the task is audit-only.

Drafted-only review can proceed. Drafted-only model training is not approved.

`draft_picks` remains the only drafted admission source because roster, player_stats, depth chart, snap, injury, and schedule appearance are post-entry context and cannot prove draft status. Draft absence remains insufficient to confirm UDFA.
