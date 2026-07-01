# Drafted Admission Source Re-Audit

Positive `draft_picks` evidence remains the only drafted-only admission source.

Historical entry-status evidence:

- Drafted rows: `1999`
- Confirmed historical UDFA rows: `0`
- Likely UDFA / needs-review rows: `2514`
- Wrong-universe rows: `138`
- Name-collision rows: `2`

The NFLVerse player-context display/update wave provides safe display context for rows passing identity gates, but roster, weekly roster, depth-chart, snap-count, player_stats, injury, schedule, contract, and identity bridge fields cannot admit a drafted row.

Drafted-only review can proceed. Drafted-only model training is not approved. `draft_picks` remains the only admission source because it directly encodes draft event evidence; appearance in other datasets is post-entry context and may leak role, availability, or production.
