# QB/TE Context Balance v1 Production Patch Proposal - 2026-06-09

This is a precise patch proposal only. No implementation or promotion occurred.

## Candidate Name
`qb_te_context_balance_v1_revised`

## Hypothesis
A production-safe QB/TE discipline patch can improve 10-team 1QB and no-TE-premium cross-position shape by applying clearer format-context discipline inside the admitted QB/TE current-value layer, while leaving RB/WR scoring, source routing, and lineage gates unchanged.

## Intended Behavior
- Reduce QB top-end domination in 1QB without burying elite private-evidence QBs below obvious depth rows.
- Reduce no-premium TE top-end inflation while preserving a narrow elite-TE exception path when private component evidence is overwhelming and explainable.
- Keep RB/WR score values unchanged in a QB/TE-only patch.
- Preserve trust, warning, source-disclosure, and sentinel behavior.

## Exact Production Files Likely Affected
- `src/services/model_v4_qb_te_current_value_service.py`
- `src/services/model_v4_current_value_checkpoint_service.py`, readback/tests only unless output schema needs a discipline receipt field
- `src/services/full_board_current_value_export_service.py`, only if the export must route a new discipline receipt
- `scripts/build_model_v4_full_board_rankings_exports.py`, rerun only

## Exact Production Functions / Classes Likely Affected
- `build_qb_te_current_value`
- `_score_row`
- `_discipline`
- `_qb_components` readback only, if the patch needs component diagnostics
- `_te_components` readback only, if the patch needs component diagnostics
- `_sanity_warnings`
- `QbTeCurrentValueResult` only if additional audit metadata is required

## Tests That Must Be Added
- QB 1QB top-25/top-10 shape test using private output only.
- TE no-premium elite-exception test using private output only.
- RB/WR score unchanged test.
- My Team movement explainability readback.
- Keenan Allen and Darius Slayton sentinel tests.
- No market/league/RotoWire projection/legacy contamination test.
- Full-board output remains 232 scored QB/RB/WR/TE and 8 unscored kickers.
- Decision Board remains blocked.

## Expected Output Files That Would Change If Approved
- `local_exports/model_v4/current_value/latest/qb_te_current_value_review_rows.csv`
- `local_exports/model_v4/current_value/latest/qb_te_current_value_component_rows.csv`
- `local_exports/model_v4/current_value/latest/qb_te_current_value_warnings.csv`
- `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv`
- `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- movement/sanity/readiness reports generated after the approved production rerun

## Rollback Plan
- Keep this shadow folder and baseline hashes as receipts.
- Revert the production patch commit if shape checks, sentinels, or contamination checks fail.
- Re-run the safe Rankings pipeline from the pre-patch commit to restore active exports.
- Do not manually copy shadow CSVs into active output paths.

## Promotion Gate Checklist
- User approval obtained before patching.
- Shadow output is not copied into active Rankings.
- Production pipeline recomputes active Rankings if approved.
- Source/lineage/sentinel/contamination gates pass.
- QB/TE movement audit passes human review.
- RB/WR scores remain unchanged except collateral rank movement.
- Decision Board remains blocked until the patched Rankings baseline is re-audited.

## Risks
- TE overcorrection: all TEs left the top 25 in shadow, and Brock Bowers fell to #67.
- QB compression may handle top-end dominance while leaving low elite-QB anomalies unresolved.
- A broad compression rule may mask whether age/status, VORP anchor, or cross-position scaling is the true cause.

## Failure Modes
- TEs become structurally undervalued in no-premium despite elite evidence.
- Elite QBs are flattened too close to replacement/depth rows.
- QB/TE patch unexpectedly changes RB/WR scores.
- Warnings/trust labels become cleaner without source repair.
- Market/league/display-only context leaks into private score tests or implementation.

## Invariants That Must Remain True
- Active baseline hash from this audit: `cf32135966d397965e8a60cef2a8e4e243fe9d18cab5d8b439157f45af010dea`.
- Keenan Allen legacy 82.4 remains comparison-only.
- Darius Slayton legacy 78.88 remains comparison-only.
- Current NWR scores use admitted Model v4 lineage only.
- 2026 5.04 remains no-baseline/no invented equivalence.
- K rows remain hidden/default-off.
- Market/league/RotoWire projection/ranking data stays out of private value.

## Candidate Acceptance Criteria For A Later Patch
- Top 25 should not be dominated by QBs in 10-team 1QB.
- No-premium TE should allow elite exceptions but avoid #1 overall TE unless component evidence is overwhelming and explainable.
- Elite QBs should not collapse below obvious depth/replacement rows without explanation.
- RB/WR score values should not change from a QB/TE-only patch.
- My Team movement should be explainable.
- No source-quarantined row should become cleaner because of formula patch.
- Sentinels remain safe.
- No contamination.
- Full focused and relevant regression tests pass.

## User Approval Required
User approval is required before any production patch. Do not promote shadow outputs directly. Recompute active Rankings only through the production pipeline if approved. Keep Decision Board blocked until Rankings patch is approved and re-audited.
