# Live Rookie Overlay

The overlay reconciles by unique official overall pick, then validates exact name,
position, and round receipts. Runtime does not perform a fuzzy or name-only join.

## Sources pinned

- Frozen Rookie Review: `06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f`
- Frozen blocker inventory: `361011524dfbabc62cecaf4286d201b219e275a5fa8b43b57c93017eca56d19a`
- Current identity/role authority: `f4ae6106f5302c59f23d83a27c006a894c5660b3058a011e5b2f16c6a2c79ff9`

The live source supplies factual ID/team/status/draft context only. It does not supply
or authorize a Dynasty Rookie Review score. Five of the 80 live IDs use a governed
registry namespace rather than GSIS shape; the schema therefore says
`live_governed_player_id` plus `live_player_id_namespace`.

Refresh alert count: **7**.
