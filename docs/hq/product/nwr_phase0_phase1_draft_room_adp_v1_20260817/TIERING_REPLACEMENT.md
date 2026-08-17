# Tiering Replacement

Global IQR bucketing was replaced with deterministic adjacent value-gap segmentation. Boundaries prefer statistically unusual replacement-value cliffs using the median adjacent gap and median absolute deviation. A maximum-size guard selects the strongest local gap when a presentation tier would become too large; tiers are not forced equal.

Overall and per-position tiers are computed separately. On the admitted 608-player Fantasy Gamers-compatible board, overall tiers contain at most 24 players and position tiers at most 14. The top 150 spans multiple meaningful tiers instead of collapsing into one giant lower bucket.

Owner labels distinguish `Elite`, `Foundation`, `Strong starters`, `Core starters`, `Flex value`, `Bench value`, `Late targets`, and explicitly numbered deep-pool tiers. No opaque ML or new player-value authority is involved.
