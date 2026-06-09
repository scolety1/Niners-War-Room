# Phase 11B Replacement And VORP Core

## Purpose

Phase 11B builds the review-only 10-team, 1QB, non-PPR, first-down scoring replacement/VORP core. It does not promote app surfaces, change active rankings, alter My Team or War Board, or unlock readiness gates.

## Outputs

- `local_exports\model_v4\replacement_vorp\latest\replacement_baselines_review.csv`
- `local_exports\model_v4\replacement_vorp\latest\player_vorp_review_rows.csv`
- `local_exports\model_v4\replacement_vorp\latest\player_vorp_component_rows.csv`
- `local_exports\model_v4\replacement_vorp\latest\player_vorp_receipts.csv`
- `local_exports\model_v4\replacement_vorp\latest\player_vorp_warnings.csv`

## League Settings

- 10-team dynasty.
- 1QB.
- Non-PPR.
- Rushing and receiving first downs score 0.4 points.
- No TE premium.
- Return yards score 1 per 30 yards.
- Return TDs score 4 points.

## Replacement Defaults

| Position | Required Starter Rank | Configured Replacement Rank | Note |
| --- | ---: | ---: | --- |
| QB | 10 | 12 | 10 teams x 1QB; conservative shallow-league fringe starter. |
| RB | 20 | 30 | 10 teams x 2RB plus flex pressure. |
| WR | 30 | 40 | 10 teams x 3WR plus flex pressure. |
| TE | 10 | 12 | 10 teams x 1TE; no TE premium. |

The admitted NFL current evidence matrix is thinner than a full league pool for QB, RB, and TE, so those positions visibly use the last available admitted player when the configured replacement rank exceeds the admitted pool count.

## Source Rules

- Phase 11A allowed-field registry is enforced before building outputs.
- No market, projection, ADP, ranking, mock, or big-board fields are consumed.
- First downs come only from admitted matched-only first-down views.
- Missing first downs are not estimated and are not labeled as direct data.
- Return production is direct scoring only, not talent or role signal.
- Review-only prior VORP context is not consumed.

## Summary

- Player rows: 80
- Baseline rows: 4
- Component rows: 320
- Receipt rows: 240
- Warning rows: 86
- Market rows used: 0
- Projection rows used: 0
- Failed sanity fixtures: 0
- Review sanity fixtures: 1

## Safety Confirmations

- Review-only outputs.
- No active rankings changed.
- No app promotion.
- No readiness unlock.
- No My Team or War Board changes.
