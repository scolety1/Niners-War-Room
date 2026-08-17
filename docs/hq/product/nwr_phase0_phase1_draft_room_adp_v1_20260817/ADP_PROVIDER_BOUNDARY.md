# ADP Provider Boundary

The first admitted provider is an owner-supplied CSV. Required columns are `player`, `position`, `overall_adp`, `source`, `scoring_format`, `team_count`, and `date`. Optional fields are `player_id`, `team`, `expected_pick`, `min_pick`, `max_pick`, and `std_dev`.

Imports are bounded to 2 MB at the service layer, require one source/scoring/date snapshot, reject future dates and league mismatches, and match only governed IDs or exact normalized identity. The source SHA-256 and unmatched identities are retained.

ADP is labeled `OWNER-IMPORTED ADP — MARKET TIMING ONLY`. It cannot change NWR rank, projection, replacement value, or tier authority. No FantasyPros key is required, no paid source is scraped, and no ADP is invented when the provider is absent. FantasyPros and lawful public providers remain future boundary implementations only.
