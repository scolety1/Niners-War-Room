# Candidate Search Scope V1

The next phase may run a limited review-only candidate search only if it follows this scope:

- Use the canonical V3 substrate.
- Use Source Contract V1 feature decisions.
- Use the fixed train/validation/holdout split from this gate.
- Rerun a frozen V3 baseline before testing candidates.
- Evaluate only declared formula families from `allowed_candidate_formula_family_matrix.csv`.
- Keep candidates interpretable and bounded.
- Keep null-fenced features out of the primary pass.
- Report position-specific metrics before aggregate metrics.
- Treat all outputs as review-only evidence.

Not allowed:

- Production promotion.
- App wiring.
- Ranking changes.
- Hidden sort.
- Recommendations.
- Source-truth promotion.
- Formula search outside declared families.
- Model training or learned weights.
