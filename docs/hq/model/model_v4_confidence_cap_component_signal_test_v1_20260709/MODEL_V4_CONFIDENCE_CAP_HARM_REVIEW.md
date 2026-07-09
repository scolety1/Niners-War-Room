# Model v4 Confidence Cap Harm Review

## Harm Checks

- Low-confidence rows: `28`
- Low-confidence rows that became startable: `1`
- Full-confidence rows that were PYF false positives: `572`
- Low-confidence startable example: `2013 WR T.Ginn` finished `35`.

## Finding

The main harm risk is semantic, not mathematical: `full_component_coverage` can be misread as player-level confidence. It is only receipt/source coverage. It does not mean the player is safe, accurate, or production-approved.

## Guardrail

Any future UI, report, or Formula Gauntlet handoff must label confidence cap as review-only coverage/missingness context. It must not be used as a standalone score, weight, rank adjustment, source promotion, or production/model-use input.