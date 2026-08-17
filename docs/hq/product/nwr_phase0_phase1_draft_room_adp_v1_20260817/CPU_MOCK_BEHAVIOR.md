# CPU Mock Behavior

With admitted ADP, CPU teams use expected pick plus deterministic seeded variation, current roster construction, open starter/FLEX needs, and late legality constraints. This prevents ten identical NWR-clone drafts while keeping runs reproducible for a given seed.

Without ADP, CPU teams use `DISCLOSED_NWR_ORDER_FALLBACK`. The Draft Room labels this as deterministic fallback rather than market realism.

CPU rosters cap unnecessary QB/TE duplication, fill legal starters and FLEX, and deterministically select real manual K/DST assets late. K/DST picks carry `MANUAL_UNMODELED`; they have no fake projection or NWR rank.
