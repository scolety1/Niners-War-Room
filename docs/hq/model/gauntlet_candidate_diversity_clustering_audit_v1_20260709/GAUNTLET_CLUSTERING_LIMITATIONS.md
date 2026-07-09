# Gauntlet Clustering Limitations

- Row-level candidate scores/ranks were not persisted by the prior Gauntlet packet, so this audit reconstructed rank vectors by importing the accepted Gauntlet runner and fixed registry.
- No new formulas were added and no weights were tuned.
- Candidate clusters use rank correlation >= `0.98` within compatible scope groups.
- Near-duplicate output pairs use rank correlation >= `0.995`.
- Position-specific candidates are allowed to remain distinct neighborhoods even when they correlate strongly with all-position production formulas on the overlapping position subset.
- Clustering is a review-only diagnostic, not model approval or ranking integration.
