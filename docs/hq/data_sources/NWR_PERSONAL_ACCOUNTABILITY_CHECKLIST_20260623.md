# NWR Personal Accountability Checklist - 2026-06-23

Use this before trusting any NWR output.

## Source And Role

- Is this based on a source-truth artifact, an NWR model output, or a candidate overlay?
- Is this source current, frozen, stale, local-only, or proxy?
- Is this player matched by stable player_id, exact name+position, or fuzzy name?
- Is the source allowed as a model input, or is it display-only/diagnostic?

## Market And Ranking Guardrails

- Are ADP, ECR, DynastyProcess values, projections, trade calculators, market ranks, or vendor ranks involved?
- If yes, are they clearly labeled display-only and excluded from model/rank logic?
- Is any market data being treated like NWR value? If yes, stop.

## Player Evidence

- Does this player have age, team, position, role/status, and player_id coverage?
- Is the player in the full dynasty board, frozen board, PDF free-agent overlay, or only an unmatched candidate row?
- Are manual-review flags or uncertainty reasons visible?
- Does current injury/news/role status require a human check?

## Outcome Columns

- Is the outcome position-applicable?
- Is wrong-position outcome hidden or N/A?
- Is same-position missing displayed as exactly `Not enough information`?
- Is missing outcome being treated as unknown rather than zero?

## Historical Support

- Is this claim backed by a verified historical backtest or only a proxy/sensitivity run?
- Did the backtest use only pre-outcome/as-of-safe features?
- Is the data season/position coverage broad enough to trust the claim?

## Draft Mode Versus Research Mode

- Is this a draft-day source of truth, a review-only decision aid, or a future research idea?
- If Final Board Rank and On-Clock/Candidate Rank disagree, did I pause for human review?
- Does the app claim final advice, or is it a review surface?

## Personal Red Flags

- Not enough information is missing or replaced by blank/zero.
- A PDF-only free agent has a confident-looking model rank without matched NWR evidence.
- A vendor/market field is not labeled display-only.
- A rookie/veteran comparison uses mixed score bases without a review-only label.
- A player has UNKNOWN/needs_data/team/status caveats but is treated as clean.
