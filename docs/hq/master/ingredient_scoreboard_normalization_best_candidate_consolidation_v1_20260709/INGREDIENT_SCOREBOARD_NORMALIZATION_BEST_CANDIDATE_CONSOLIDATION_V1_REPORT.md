# Ingredient Scoreboard Normalization / Best Candidate Consolidation V1 Report

## Verdict

`YELLOW_SCOREBOARD_NORMALIZED_RANKING_SIM_NOT_READY`

## Scope

This packet normalizes accepted ingredient results into three separate scoreboards: full-history comparable, broad-window comparable, and partial-window modern. It prevents partial ffopportunity/NGS windows from being compared directly against the full-history `.755` plateau or the snap/depth broad-window `.763` reference.

## Lanes Included

- PFR RB broken tackle
- nflverse advanced ingredient audit
- ffopportunity / NGS autonomous V2
- nflverse EPA/opportunity
- nflverse receiving opportunity
- nflverse snap/depth role
- point-in-time injury availability

## Best By Scoreboard

- Full-history best: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100` from `nflverse snap/depth role`, Spearman `0.758`, rows `5518`.
- Broad-window best: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100` from `nflverse snap/depth role`, Spearman `0.763`, rows `5122`.
- Partial-window best: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10` from `ffopportunity / NGS autonomous V2`, Spearman `0.790`, rows `1740`.

## Interpretation

- No result materially beats the full-history `.755` plateau. Injury/availability reaches `.757`, but the lift is only about `.002` and does not beat the stronger snap/depth broad-window reference.
- Snap/depth remains the best broad-window additive result at `.763` on `2014-2025`, `5,122` rows.
- Partial-window modern combinations remain promising around `.789-.790`, but they depend on ffopportunity/NGS-era windows and are not full-history-comparable.
- No comparable row set materially beats snap/depth `.763`.
- Review-only ranking simulation is not justified.

## Next Lane

Recommended next single lane: `Historical Market / ADP Source Gate and Data Mart Join V1`.

This should be a source/as-of gate and sidecar join lane, not a ranking simulation and not production model-use.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior changed: no.
- Push/merge performed: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
