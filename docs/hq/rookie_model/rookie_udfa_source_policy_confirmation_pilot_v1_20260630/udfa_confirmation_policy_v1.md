# UDFA Confirmation Policy V1

This policy is conservative by design. It is a review-only gate for historical rookie entry status and does not approve training, model use, current-player scoring, Gate F, Gate G, or Rankings wiring.

## Minimum Standard For `confirmed_udfa`

A row may be proposed for `confirmed_udfa` only when all of the following are true:

1. The player identity match is high confidence across available identifiers.
2. A reliable source confirms the player entered the NFL as a rookie free agent or UDFA in that rookie class.
3. A reliable draft-pick lookup confirms the player was not selected in that same draft class.
4. There is no unresolved same-name collision, position conflict, school/timeline conflict, duplicate ID, or class-year ambiguity.
5. No future NFL production, games, starts, AV, awards, career length, fantasy outcome, or Outcome V2 label is used to establish entry status.
6. A human/manual approval gate accepts the source evidence before any original artifact is patched.

`confirmed_udfa_candidate` in this lane means eligible for human review/promotion proposal only. It is not model-approved.

## Evidence Hierarchy

1. Approved official draft-pick data for drafted exclusion.
2. Approved official/team/NFL transaction or roster-signing evidence that explicitly identifies rookie free-agent or undrafted-free-agent entry in the class.
3. Approved high-confidence identity bridge tying the evidence to the correct player.
4. Review-only registry/player ID evidence as candidate support only.
5. Manual lookup notes only after a future citation and human-review policy is approved.

## Acceptable Source Types

- nflverse/nflreadpy draft picks for proving drafted status or draft absence in a specific class.
- Future approved official/team transaction artifacts that explicitly state rookie free-agent or UDFA entry.
- Future approved manual-review packets with cited evidence and identity resolution.

## Blocked Source Types

- Draft absence alone.
- NFL appearance, player_stats, games, starts, seasons played, AV, awards, fantasy output, or career length.
- Outcome V2 labels.
- Market rankings, ADP, projections, DynastyProcess values, Gmail, vendor/private/proxy notes, RotoWire, FantasyPros, scraped FootballDB, or any raw/private source.

## Why Draft Absence Alone Is Insufficient

Not being found in draft-pick data proves only that the current lookup did not find a drafted selection. It does not prove the player was a rookie entrant, that the class year is correct, or that the identity bridge is clean.

## Why NFL Stats Or Appearance Alone Is Insufficient

NFL appearance evidence can identify possible entrants, but it can also reflect later free-agent appearances, replacement players, roster churn, or identity ambiguity. It cannot establish rookie entry status without an approved entry source.

## Why Outcome V2 Labels Cannot Confirm Entry Status

Outcome V2 labels are evaluation targets. Using them to prove entry status would leak future information and collapse label evidence into source-truth evidence.

## Fake Round 8 And Missing Values

Fake round 8 is prohibited. Missing draft capital must remain blank, unknown, or `Not enough information`; it must never become `0`, `false`, clean, low-risk, or confirmed undrafted.

## Identity And Timeline Handling

- Missing IDs require human identity review before promotion.
- Same-name collisions block promotion.
- Position mismatch blocks promotion until resolved.
- Class-year ambiguity routes to `free_agent_rookie_needs_review` or `unknown`, not `confirmed_udfa`.
- Free-agent rookie vs UDFA ambiguity remains blocked unless the approved source explicitly resolves it.

## What Remains Blocked

All rows remain `review_only=true`, `model_use_allowed=false`, and `training_allowed=false`. This policy does not authorize UDFA modeling, combined drafted/UDFA modeling, Gate F release, Gate G release, or app wiring.
