# Games Missed Feasibility Report

Verdict: `BLOCKED_NOT_ENOUGH_INFORMATION`

## Current Feasibility

`games_missed_while_rostered` cannot be represented safely from the current
tracked artifacts.

Evidence:

- Denominator artifact rows: `588`
- `games_missed_while_rostered` safe rows: `0`
- `games_missed_while_rostered` missing rows: `588`
- Current display approval: `false`
- Current experiment approval: `false`
- Current model approval: `false`
- Current training approval: `false`
- Current source-truth approval: `false`
- Current health inference approval: `false`

## Why Current Evidence Is Insufficient

The current denominator artifact can show supported rostered-game denominators
and positive snap/stat evidence. It cannot prove missed games because absence of
a snap or stat row can mean many different things:

- player had no recorded snap row in the source extract
- player had no recorded stat row in the source extract
- player was active without usage or without a stat
- player was inactive for a non-injury reason
- player was on injured reserve or another roster status not resolved by this artifact
- weekly roster or schedule evidence was missing or censored
- the game was a bye week or schedule exception
- identity was not approved
- injury report data was absent
- source coverage or timing was incomplete

None of those cases may be collapsed into a missed game.

## Could It Ever Be Represented Safely?

Only with a future evidence lane that supplies strict point-in-time proof. The
minimum future proof would need:

1. A factual game-status hierarchy for every player-game candidate.
2. Explicit active, inactive, injured reserve, practice squad, suspended, and
   unavailable states where the source supports them.
3. Schedule handling for bye weeks, postponements, cancellations, neutral site
   games, and postseason exclusion.
4. Rostered-at-game eligibility rules with as-of timestamps.
5. Snap and stat absence rules proving they are never used as missed-game proof.
6. Injury-report absence rules proving missing injury rows are never healthy
   rows.
7. Identity-safe joins only.
8. Row-level censoring states that preserve `Not enough information`.
9. Historical replay and leakage diagnostics before any experiment request.

Even if those future proofs exist, this packet would still not approve model,
training, source truth, ranking, hidden sort, recommendation, trade value, or
pick value use.

## Current Rule

Display `games_missed_while_rostered` as `Not enough information`.
