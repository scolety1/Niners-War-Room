# Sparse-History Population Definition

The review-only sparse-history population is any player-season matching one or more of these conditions:

- true rookie: `years_since_draft = 0`
- second-year player: `years_since_draft = 1`
- third-year player: `years_since_draft = 2`
- low prior games: fewer than `8` prior games or the Formula Data Mart low-games flag is true
- low prior snaps: fewer than `300` prior offensive snaps
- low prior fantasy points: missing PYF or fewer than `75` prior NWR points
- no usable PYF: missing PYF score/rank
- sparse multi-year production: fewer than two prior years for two-year production or fewer than three prior years for three-year production
- role-promotion sparse-history player: sparse base plus prior-season snap/depth role signal
- availability-rebound sparse-history player: sparse base plus clean/rebound availability signal

Separated review buckets:

- true rookies
- second-year breakout candidates
- third-year breakout candidates
- veterans with sparse recent history
- injury-rebound sparse-history players
- role-promotion sparse-history players

These are design/test buckets only. They are not production ranking logic.
