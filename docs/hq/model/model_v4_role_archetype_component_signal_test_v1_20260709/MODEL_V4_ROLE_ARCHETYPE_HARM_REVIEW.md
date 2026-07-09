# Model v4 Role Archetype Harm Review

## Harm Checks

- Sparse-history rows that became startable: `48`
- Low/sparse archetype rows that became startable: `55`
- High-volume archetype PYF false positives: `468`

## Finding

The main harm risk is over-interpreting archetypes. Sparse or low-volume archetypes can still break out, while high-volume archetypes can still collapse. The labels should be used for review slices and caution flags, not hard penalties, boosts, or rankings integration.

## Guardrail

Any future Formula Gauntlet handoff must preserve archetypes as review-only context and compare against PYF, low-games, sparse-history, and prior-decline miss patterns.