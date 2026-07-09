# Data Hygiene Escalation Rules

Data Hygiene must escalate to Master HQ when an evidence packet could affect canonical project decisions.

## Escalate To Master HQ When

- a source might be promoted
- a formula might use a new input
- a board/ranking may be considered production-active
- a replay/benchmark may support promotion
- app/runtime behavior may change
- multiple lanes conflict
- review-only evidence may become model-use
- source-truth status may change
- canonical merge/canonicalization is needed
- a remote push is requested
- a production accuracy claim is being considered

## Data Hygiene May Continue Without Escalation When

- work is docs-only evidence gathering
- an artifact is being classified as review-only, display-only, blocked, identity-unsafe, leakage-unsafe, or not enough information
- the output is a receipt-chain audit, join audit, missingness audit, leakage audit, rebuild audit, or handoff packet
- no app/runtime/model/rank/formula/source-truth behavior changes

## Stop Conditions

Stop and hand off when the next action would:

- approve production/model use
- promote a source
- change app behavior
- change ranking or hidden sort behavior
- run formula tournaments
- tune weights
- write latest pointers
- merge or push without explicit approval
- substitute missing data with guesses
- approve name-only joins
