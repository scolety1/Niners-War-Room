# Rankings Outcome Lens Safe Upgrade

Date: 2026-06-30

## Verdict

`GREEN_DISPLAY_ONLY_UX_UPGRADE`

This lane updates Dynasty Rankings Outcome Lens status language only. It does
not add probability columns, model inputs, source-truth gates, hidden sort keys,
rank changes, tier changes, trade value, pick value, Live Draft behavior, or Mock
Draft behavior.

## Approved UX Change

The Outcome Lens now distinguishes:

- `RB_T6_WITHIN_5Y`: weak-calibration blocked; display as `Not enough information`.
- `RB_T12_WITHIN_5Y`: historical 2000-2024 review-only approved, but not
  current-player activated; display as `Not enough information` unless a future
  current-player artifact/gate explicitly approves it.

The existing active Outcome V2 current-player fields remain unchanged.

## Not Activated

The 2000-2024 historical Outcome V2 evidence is review-only. It does not activate:

- current-player probabilities
- app-facing nflverse factual context
- Rankings integration for new fields
- model input
- source truth
- hidden sort
- Dynasty Rank
- Final Board Rank
- tiers
- trade value
- pick value

## Preserved Behavior

- Default sort remains Dynasty Rank ascending.
- Market Baseline remains display-only.
- Missing outcome, injury, usage, or feature data remains `Not enough information`.
- Missing injury/usage/depth context is not clean health or clean role certainty.
- Clean Board keeps outcome columns hidden.
- Outcome Lens remains the only Rankings surface for Outcome V2 display context.

## Human Review Checklist

- Open `/rankings`.
- Select `Outcome Lens`.
- Confirm the Outcome V2 callout says historical validation is review-only.
- Confirm RB T6 Within 5Y and RB T12 Within 5Y are not active probability columns.
- Confirm missing values say `Not enough information`.
- Confirm Clean Board remains clean.
- Confirm default sort remains Dynasty Rank.
