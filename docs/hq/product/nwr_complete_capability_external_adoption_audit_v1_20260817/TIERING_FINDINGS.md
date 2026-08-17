# Tiering Findings

Current Redraft tiering computes adjacent value gaps, derives a global threshold of `max(5, median + 1.5 × IQR)`, and starts a new tier at every gap meeting it. This is deterministic but brittle: one scale and threshold span all positions/board regions, minimum/maximum tier sizes are unconstrained, and owner evidence already observed a one-player Tier 1 and oversized Tier 14.

## Replacement

Use a deterministic, position-first hybrid:

1. Sort by the governed value appropriate to the surface.
2. Normalize adjacent gaps locally within position and board band.
3. Identify stable cliffs through robust z/MAD or change-point segmentation.
4. Enforce documented minimum evidence, not arbitrary minimum player count; merge statistically indistinguishable micro-segments.
5. Validate stability across projection refreshes and plausible scoring perturbations.
6. Present every boundary with the value gap and confidence.

Overall tiers may then be composed from position tiers plus replacement value for draft UX. Hierarchical clustering is acceptable as an offline comparison, not an opaque production authority. Fixed-`k` KMeans is rejected.

Use `1A/1B/1C` only when a supported within-tier separation improves a decision. Otherwise keep one tier. Labels are presentation, not new authorities.
