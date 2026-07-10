# Blockers And Caveats

- This is review-only evidence, not production/model-use.
- Same-season/future context was not used; all tests use feature season N to target season N+1.
- Snap counts use public `players.parquet` PFR-to-GSIS identity mapping; this is review-only and not source promotion.
- 2012 snap-count data is effectively unavailable, so snap-only fields have lower 2013 target coverage. Depth-chart fields cover the full target window through feature season 2012.
- Combo tests using prior ffopportunity or NGS inherit partial-window V2 sidecar caveats.
- Partial-window results cannot be used to claim the full-history `.755` plateau was broken.
- Review-only ranking simulation remains blocked.
