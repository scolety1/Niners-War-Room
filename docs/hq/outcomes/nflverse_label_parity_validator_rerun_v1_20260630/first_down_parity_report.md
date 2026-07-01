# First-Down Parity Report

## Result

`PARTIAL_FIRST_DOWN_COMPONENT_ONLY_NOT_FULL_SCORING_RECOMPUTE`

The sidecar contains explicit nonzero first-down component rows for:

- `passing_first_downs`
- `rushing_first_downs`
- `receiving_first_downs`

The admitted Outcome labels use `exact_verified_first_downs` scoring, so the sidecar stat heads are compatible as review evidence. However, the sidecar does not include all scoring inputs, all player-week rows, or explicit zero rows. Therefore this rerun cannot recompute full fantasy scoring parity.

## Matched evidence

- Direct same-season sidecar row records matched: `6,372`
- Direct same-season unique sidecar row IDs matched: `3,186`
- Matched sidecar-label rows written: `25,488`
- Matched-row artifact SHA256: `41b4af6b0cea6810fd8e0feb6ae62d58ae6547794fa935513dfb0ae9623f5569`

## Guardrail

Sidecar rows remain comparison substrate only. They are not labels, not probabilities, and not model features.
