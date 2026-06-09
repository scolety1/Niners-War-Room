# Sprint 12/13 Review-Only External Audit Prompt

You are auditing Model v4 Sprint 12 and Sprint 13 for a local-first dynasty fantasy football project.

League format:
- 10-team dynasty
- 1QB
- non-PPR
- first-down scoring
- no TE premium

Context:
- Phase 10 data spine passed renewed pre-formula audit.
- Phase 11A formula contract and allowed-field registry were created.
- Phase 11B replacement/VORP core was created.
- Phase 11C through 11G built review-only current player value layers.
- Phase 11G external audit cleared the project for the next formula stage.
- Sprint 12/13 are still review-only and must not be treated as final rankings, recommendations, or active app outputs.

Please audit the attached packet and verify:
1. Sprint 13 prospect value uses only `admitted_prospect_current_feature_matrix.csv` for private football value.
2. Review-only prospects are not consumed.
3. Market, ADP, rankings, projections, mock drafts, big boards, and consensus ranks do not drive private football value.
4. Prospect components are source-labeled and receipt-backed.
5. Missing prospect evidence remains missing and creates warnings or confidence caps, not zero/average/positive evidence.
6. Workout missingness repair from Phase 10Q remains respected.
7. Sprint 12 unified dynasty asset value keeps current players, current prospects, and rookie picks separable by source layer.
8. Pick values are clearly heuristic review-only baselines, not trade recommendations.
9. Current player values still trace back to Phase 11G and retain QB/TE VORP discipline.
10. The outputs do not change active app rankings, My Team, War Board, readiness gates, or promotion status.

Audit verdict options:
- safe_to_continue_review_only_formula_work
- needs_prospect_formula_repair
- needs_pick_value_repair
- needs_leakage_repair
- needs_source_or_identity_repair
- needs_architecture_repair

Please include:
- critical blockers
- high-risk issues
- medium-risk cleanup
- suspicious rows or unsupported components
- whether Sprint 12/13 can move to the next review-only sprint after fixes
