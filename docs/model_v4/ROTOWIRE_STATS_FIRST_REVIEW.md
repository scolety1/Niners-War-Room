# RotoWire Stats-First Review

Date: 2026-05-17

## Verdict

The RotoWire stats-first layer is ready as a review-only evidence preview. It is
not a final dynasty ranking and must not be promoted directly into My Team, War
Board, Rankings, Draft Board, or League Targets.

The layer answers one narrow question: "What do the structured RotoWire NFL
stats and role evidence say before dynasty age, rookie priors, roster rules,
market context, and final decision thresholds are applied?"

## Outputs

Generated under:

`local_exports/model_v4/rotowire_stats_first/latest`

| Output | Rows |
| --- | ---: |
| `rotowire_stats_first_value_rows.csv` | 80 |
| `rotowire_stats_first_component_rows.csv` | 462 |
| `rotowire_stats_first_warning_rows.csv` | 25 |
| `rotowire_stats_first_summary.csv` | 13 summary metrics |

## Inputs Used For Core Value

- historical RotoWire passing/rushing/receiving stats
- locally recomputed LVE base scoring without first-down points
- RotoWire red-zone role
- RotoWire snap role
- RotoWire target and alignment role
- licensed RotoWire route/receiving advanced metrics

## Inputs Not Used For Core Value

- RotoWire projections
- ADP
- cheat-sheet rankings
- dynasty rankings
- league rank
- market/liquidity
- injury absence as healthy evidence

## Format Correction

The first raw output exposed a known cross-position problem: if every position
is normalized internally and then compared directly, the best TE or QB can look
like the best overall asset. That is wrong for this league.

The review layer now applies explicit 10-team, 1QB, no-TE-premium format
multipliers:

| Position | Multiplier |
| --- | ---: |
| RB | 1.00 |
| WR | 0.96 |
| QB | 0.72 |
| TE | 0.62 |

This is a format correction, not a decision-ready dynasty formula.

## Current Top Evidence Rows

After format correction, the top stats-first evidence rows begin with:

- Bijan Robinson
- Jahmyr Gibbs
- Jonathan Taylor
- Drake London
- George Pickens
- Davante Adams
- Puka Nacua
- Derrick Henry
- Tee Higgins
- Christian McCaffrey

Interpretation: this is historical football evidence only. Older veterans can
still appear high because age/dropoff has not been applied yet.

## Named-Player Notes

- Bijan Robinson and Jahmyr Gibbs now lead the evidence layer, which is a good
  sign for RB/RB sanity.
- Jaxon Smith-Njigba, Puka Nacua, and CeeDee Lamb are strong stats/role rows.
- Ja'Marr Chase, Justin Jefferson, and Amon-Ra St. Brown are lower than dynasty
  sanity beliefs would expect, so the final formula must inspect whether 2025
  RotoWire context, missing first-down scoring, injuries, or weighting explains
  the gap.
- De'Von Achane is RB9 in this layer, not because he is a weak dynasty asset,
  but because this layer is still stats/role evidence before dynasty asset
  priors, age curve, explosive profile, and roster-decision rules.
- Brock Bowers is suppressed for no-TE premium and remains review due sourced
  injury context.
- Incoming rookies remain weak/review until the rookie/prospect layer is built.

## Remaining Work Before App Promotion

1. Add the dynasty asset layer on top of stats-first evidence:
   - age/dropoff
   - RB fragility
   - WR target-earning stability
   - QB 1QB suppression
   - TE no-premium suppression
   - young bridge / rookie prior
2. Add rookie/prospect evidence from the user upload area.
3. Re-run sanity fixtures against the RotoWire-powered preview.
4. Produce a RotoWire-specific named-player audit.
5. Run an external audit before any app promotion.

## Guardrails

- Active rankings unchanged.
- My Team unchanged.
- War Board unchanged.
- No readiness gates unlocked.
- RotoWire stats-first outputs are review-only.

