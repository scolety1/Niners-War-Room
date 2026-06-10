# QB Age/Horizon Sanity Audit - 2026-06-10

## Scope

This is a shadow-only audit for old quarterback dynasty horizon risk after the WR/QB v2 promotion. It does not undo WR/QB v2, does not promote any new score, and does not use market rank, league rank, ADP, consensus, projections, trade calculators, RotoWire rankings/projections, prior draft history, or legacy active-pack private score.

## Why Matthew Stafford Is Still High

Matthew Stafford is around `#40` because the active Model v4 current-value board gives him a strong current private QB component:

- Position: `QB`
- Active rank/score: `#40 / 37.1191`
- Role archetype: `qb_pocket_leaning`
- Positive VORP points: `43.9`
- Review scoring points: `284.0`
- Imported first-down points: `0.0`
- Discipline multiplier: `0.6743`
- Lifecycle modifier: `1.0`
- Confidence cap: `1.0`
- Warning flags: `first_down_missing_confidence_cap|one_qb_context_balance_upper_band_guard_v2`

The problem is not the WR/QB v2 promotion. Stafford did not receive a QB v2 elite floor lift. His issue is that current passing/VORP evidence remains high while the active full-board row lacks a meaningful old-pocket dynasty horizon discount. The factual age sidecar has Stafford at `38.3`, but the active QB lifecycle row does not currently apply an old-pocket age/retirement cap.

## Nearby QB Sanity

Current active QB order after WR/QB v2:

- Josh Allen `#21`
- Drake Maye `#23`
- Trevor Lawrence `#28`
- Matthew Stafford `#40`
- Jalen Hurts `#50`
- Justin Herbert `#51`
- Caleb Williams `#52`
- Bo Nix `#63`
- Patrick Mahomes `#68`
- Dak Prescott `#71`
- Jared Goff `#102`
- Baker Mayfield `#131`
- Lamar Jackson `#144`
- Aaron Rodgers `#191`
- Joe Burrow `#199`
- Jayden Daniels `#180`

Stafford is the clear outlier: he is a 38.3-year-old pocket passer with no imported first-down/rushing evidence and ranks ahead of younger or more horizon-safe QB profiles. Rodgers is already below the proposed old-pocket cap. Kirk Cousins and Russell Wilson are not active full-board rows.

## Shadow Cap Tested

Output folder:

`local_exports/model_v4/current_value/candidates/qb_age_horizon_shadow/`

Shadow files:

- `shadow_qb_age_horizon_rankings.csv`
- `shadow_qb_age_horizon_qb_movement.csv`
- `shadow_qb_age_horizon_watch_rows.csv`
- `shadow_qb_age_horizon_gate_report.csv`
- `shadow_qb_age_horizon_summary.csv`

General rule tested:

- Applies only to QBs.
- Requires factual age evidence from the local age sidecar.
- Applies mainly to age-37-plus `qb_pocket_leaning` profiles.
- Does not apply to rushing/hybrid QB profiles.
- Does not use market, ADP, public rankings, projections, trade calculators, RotoWire rankings/projections, prior draft history, or legacy private scores.
- Does not hardcode Stafford or any named QB.

Cap shape:

- Age 37-39 pocket QB with weak first-down/rushing receipt: cap at `23.5`.
- Age 40-plus pocket QB with weak first-down/rushing receipt: cap at `12.0`.
- Higher first-down/retained-value receipts can soften or block the cap.

## Watch-Row Movement

| Player | Age | Base Rank | Shadow Rank | Score Delta | Result |
|---|---:|---:|---:|---:|---|
| Matthew Stafford | 38.3 | 40 | 91 | -13.6191 | old-pocket cap applied |
| Aaron Rodgers | 42.4 | 191 | 191 | 0.0 | already below age-40 cap |
| Kirk Cousins | - | absent | absent | - | not active board row |
| Russell Wilson | - | absent | absent | - | not active board row |
| Dak Prescott | 32.8 | 71 | 70 | 0.0 | under old threshold |
| Jared Goff | 31.6 | 102 | 102 | 0.0 | under old threshold |
| Baker Mayfield | 31.1 | 131 | 131 | 0.0 | not old pocket capped |
| Patrick Mahomes | 30.6 | 68 | 67 | 0.0 | not old pocket capped |
| Lamar Jackson | 29.3 | 144 | 144 | 0.0 | rushing profile not capped |
| Josh Allen | 30.0 | 21 | 21 | 0.0 | hybrid/rushing profile not capped |
| Jalen Hurts | 27.8 | 50 | 49 | 0.0 | hybrid/rushing profile not capped |
| Joe Burrow | 29.4 | 199 | 199 | 0.0 | under old threshold |
| Jayden Daniels | 25.4 | 180 | 180 | 0.0 | under old threshold |
| Drake Maye | 23.7 | 23 | 23 | 0.0 | hybrid/rushing profile not capped |
| Trevor Lawrence | 26.6 | 28 | 28 | 0.0 | hybrid/rushing profile not capped |

Small rank deltas like `-1` for Hurts/Mahomes/Dak are sorting side effects from Stafford moving down, not score changes.

## Gates

All shadow gates passed:

- Active rows unchanged: `240`.
- Banned scoring input count: `0`.
- Non-QB score changes: `0`.
- Stafford cap applied through general rule.
- Elite/rushing QB profiles not crushed.
- Historical rookie replay metrics not recomputed because they do not validate old-veteran QB aging.

## Historical Metric Caveat

The current model-edge historical harness is rookie replay data. It can test QB rookie promotion/underpromotion, but it cannot prove whether 38- to 42-year-old veteran pocket QB horizon risk is calibrated. For this audit, historical metrics are therefore treated as unchanged/not directly applicable rather than as evidence for promotion.

Needed future data:

- Historical veteran QB age-season outcomes in this league format.
- 1QB retained-value decay by age and archetype.
- Pocket-vs-rushing QB startability and multi-year hold value.

## Recommendation

Recommendation after user approval: `promote_old_pocket_qb_horizon_guardrail`.

The shadow cap improves current-board credibility by fixing the Stafford outlier without touching WR/QB v2, RBs, TEs, younger pocket QBs, or elite/rushing QBs. The user explicitly approved promoting this as a source-safe domain-logic patch for old pocket QBs in a 10-team 1QB league.

Follow-up research still needed:

1. Add a small veteran-QB age/horizon historical dataset.
2. Re-test retained-value decay by age and archetype once that data exists.
