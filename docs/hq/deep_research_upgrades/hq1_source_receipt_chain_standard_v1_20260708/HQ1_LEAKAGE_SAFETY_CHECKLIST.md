# HQ1 Leakage Safety Checklist

Use this checklist before any historical validation, replay, feature tournament, Formula Gauntlet candidate, HQ2 challenger, source admission, or ranking evidence lane.

## Decision-Date Contract

- [ ] Target season is defined.
- [ ] Feature season is defined.
- [ ] Decision date is defined.
- [ ] Only information available by the decision date is eligible as an input.
- [ ] Labels are stored separately from features.

## Prohibited Historical Inputs

- [ ] No target-season outcome labels as features.
- [ ] No current roster/status/injury/depth chart context backfilled into historical seasons.
- [ ] No current rankings, market values, ADP, projections, or analyst ranks used as source truth.
- [ ] No future team, schedule, role, coaching, or transaction information as historical input.
- [ ] No current-only player metadata used to force uncertain historical identity matches.

## Source Timing

- [ ] Acquisition timestamp is recorded.
- [ ] Source publication date or version is recorded when available.
- [ ] Retroactive updates are documented.
- [ ] Point-in-time source receipts exist for injury, depth chart, roster, and availability context.
- [ ] Current webpages without historical snapshots are not treated as historical truth.

## Joins And Identity

- [ ] Join keys are available at the decision date.
- [ ] Name-only joins are not approved joins.
- [ ] Manual identity review rows are isolated.
- [ ] Ambiguous joins do not silently enter model features.

## Missingness

- [ ] Missingness is explicit.
- [ ] Coverage changes by season are documented.
- [ ] Eligibility thresholds are documented.
- [ ] Missing fields are not silently converted to zeros.
- [ ] Missing component penalties or caps are documented before scoring.

## Output Boundary

- [ ] Review-only outputs are not routed to production paths.
- [ ] Display-only fields are not treated as model inputs.
- [ ] Blocked fields remain excluded.
- [ ] Any future promotion requires a separate lane.

## Leakage Verdict

Choose one:

- `LEAKAGE_SAFE_FOR_REVIEW`: Evidence supports review-only use under the stated decision-date contract.
- `LEAKAGE_SAFE_FOR_DISPLAY_ONLY`: Evidence supports display context only.
- `LEAKAGE_RISK_UNRESOLVED`: More source timing or identity proof is needed.
- `LEAKAGE_UNSAFE`: Current/future information contaminates the feature path.
- `NOT_ENOUGH_INFORMATION`: Timing evidence is insufficient.
