# Model v4 / Phase 11G Current Value External Audit Prompt

You are auditing a local-first dynasty fantasy football model for a 10-team, 1QB, non-PPR league with first-down scoring and no TE premium.

The packet contains review-only Model v4 Phase 11 outputs. Do not assume any output is promoted to the active app. The active rankings, My Team, War Board, and readiness gates should remain unchanged.

## Audit Goal

Determine whether the Phase 11 current-value implementation is safe and football-sensible enough to proceed to the next formula stage, or whether it needs repair first.

## Files To Review

Start with:

- `docs/PHASE_11A_FORMULA_CONTRACT.md`
- `docs/PHASE_11B_REPLACEMENT_VORP_CORE.md`
- `docs/PHASE_11C_RB_WR_CURRENT_VALUE.md`
- `docs/PHASE_11D_QB_TE_CURRENT_VALUE.md`
- `docs/PHASE_11E_LIFECYCLE_ARCHETYPE_LAYER.md`
- `docs/PHASE_11F_CONFIDENCE_MISSINGNESS_LAYER.md`
- `docs/PHASE_11G_CURRENT_VALUE_CHECKPOINT.md`
- `docs/PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md`, if present

Then inspect:

- `formula_contract/formula_allowed_field_registry.csv`
- `formula_contract/formula_blocked_field_registry.csv`
- `formula_contract/formula_loader_guard_report.csv`
- `replacement_vorp/*.csv`
- `current_value/current_player_value_review_rows.csv`
- `current_value/current_player_value_component_rows.csv`
- `current_value/current_player_value_receipts.csv`
- `current_value/current_player_value_warnings.csv`
- the Phase 11C/11D/11E/11F source layer CSVs under `current_value/`
- `evidence_context/evidence_matrix_summary.csv`
- `evidence_context/source_coverage_matrix.csv`
- `evidence_context/warning_matrix.csv`
- `evidence_context/nfl_player_current_evidence_matrix.csv`

Raw paid/source exports are intentionally excluded.

## Questions To Answer

1. Does Phase 11A successfully prevent generic JSON slurping and market/projection/ranking leakage?
2. Does Phase 11B implement replacement/VORP in a way that fits a 10-team, 1QB, non-PPR, first-down league?
3. Do RB/WR current-value formulas make football sense and avoid overfitting to one stat family?
4. Do QB/TE current-value formulas enforce 1QB and no-TE-premium discipline?
5. Are lifecycle modifiers explainable and correctly limited when age, injury, route, or athletic evidence is unavailable?
6. Does the confidence layer cap missing, partial, review-only, stale, identity-risk, and source-limited evidence without turning missing data into zero, average, or positive evidence?
7. Does Phase 11G combine RB/WR, QB/TE, lifecycle, and confidence layers transparently, with all components still visible and separable?
8. Are any market, ADP, projection, ranking, mock, big-board, consensus, or league-rank fields driving private football value?
9. Are source-limited or review-only fields blocked from private value unless explicitly allowed?
10. Do receipts support each component well enough for audit?
11. Do warning rows expose the right risks, or are important risks hidden?
12. Do named-player sanity checks make football sense for:
    - Christian McCaffrey
    - Lamar Jackson
    - Josh Allen
    - Brock Purdy
    - Puka Nacua
    - Jaxon Smith-Njigba
    - Ja'Marr Chase
    - Brock Bowers
    - George Kittle
    - the Niners roster
13. Are there suspicious rankings or checkpoint scores that suggest formula, source, confidence-cap, or integration bugs?
14. Is the checkpoint safe to proceed from, or should Phase 11 require repair before moving on?

## Desired Output

Return:

1. Verdict:
   - ready for next formula stage
   - needs formula repair
   - needs source/receipt repair
   - needs confidence/lifecycle repair
   - needs architecture repair
2. Critical issues, if any
3. High-priority issues, if any
4. Medium/low issues, if any
5. Named-player sanity notes
6. Leakage/source-trust findings
7. Specific recommended next steps

Please be skeptical. Do not reward outputs for matching opinions. Evaluate whether the math, evidence lanes, source labels, receipts, and guardrails are internally safe.
