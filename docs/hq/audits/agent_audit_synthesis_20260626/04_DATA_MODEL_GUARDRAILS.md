# Data / Model / Evidence Guardrail Requirements

## Core rule

Review evidence is not model truth.

Even when an agent says APPROVE, that means the row is useful for review. It does not mean:

- `approved_by_human=true`
- `model_use_allowed=true`
- `training_allowed=true`
- source truth
- draft-room decision logic
- rank changes
- hidden sort changes

## Required validators

### Review-only flags

Validate these across CFBD Agent 1, Agent 2, and Agent 3 outputs:

- `model_use_allowed=false`
- `training_allowed=false`
- `review_only=true`
- `approved_by_human=false` where column exists

### Blocked-field scanner

Fail if any blocked field enters model/rank/training/hidden sort logic:

- DynastyProcess values
- ADP
- ECR
- market rank/value/gap
- vendor projections/ranks
- true routes
- TPRR
- YPRR
- Outcome display probabilities
- CFBD review-only production fields
- NFL usage review-only fields before gate
- Gmail raw/body evidence
- proxy drop labels

### Missingness

Missing values must not become zero/clean/average.

Required behavior:

- missing age => `Not enough information`
- missing injury/status => `Not enough information`, not healthy
- missing outcome => `Not enough information`, not zero probability
- missing player_id => blocked from identity joins
- unknown production => unknown, not low production

### Evidence promotion workflow

A future field cannot move forward unless it passes explicit stages:

1. review-only
2. display-only
3. model-candidate
4. approved model input

Promotion requires:

- human approval where identity-sensitive
- coverage report
- leakage analysis
- licensing/source policy check
- backtest/ablation where relevant
- explicit user approval gate

## Blocked now

- CFBD model input
- NFL usage model input
- decision-page wiring
- true routes / true TPRR / true YPRR
- vendor/RotoWire/FantasyPros data
- Gmail raw/body automation
- hosted deployment
- historical proxy/inferred rows as training truth
