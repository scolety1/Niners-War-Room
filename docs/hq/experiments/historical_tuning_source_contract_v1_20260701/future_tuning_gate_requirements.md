# Future Tuning Gate Requirements

The next eligible lane is `Historical Formula Tuning Readiness Gate V1`.

The gate must confirm all of the following before any candidate search:

1. The V3 source-semantics matrix and Source Contract V1 are accepted as sufficient review-only inputs.
2. The 18 `ALLOW_REVIEW_ONLY` features remain review-only and not production-approved.
3. The four optional fields remain null-fenced: `prior_offensive_snaps`, `prior_offense_pct`, `prior_receiving_air_yards`, and `prior_receiving_yards_after_catch`.
4. Red-zone sidecars remain blocked/absent unless separately admitted in a future source gate.
5. Ambiguous `rz_att` remains blocked.
6. Routes, TPRR, YPRR, and route proxy families remain blocked.
7. Market, ADP, vendor, projection, and rank fields remain blocked as source truth.
8. Missing values are not filled with zero unless an admitted source proves explicit zero semantics.
9. No current-only roster, status, injury, depth, or schedule context is used as historical feature data.
10. Candidate outputs, if ever produced, remain candidate-only and not production-approved.
