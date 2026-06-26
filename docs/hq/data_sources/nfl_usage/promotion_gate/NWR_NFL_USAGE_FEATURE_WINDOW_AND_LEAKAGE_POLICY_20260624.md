# NFL Usage Feature Window And Leakage Policy

## Legal Predictive Window

Season N usage fields may predict season N+1 outcomes only after season N stats are finalized and the target window is strictly future.

## In-Season Research Window

Player-week windows may be used only when the feature cutoff predates the target weeks. Full-season aggregates are illegal for same-season final targets.

## Grain

The promotion gate supports player-week, player-game, and player-season summaries. Future predictive runs must declare the grain before fitting or scoring.

## Rolling Windows

Rolling 4-week, 8-week, and season-to-date windows are allowed only when computed from weeks before the target period.

## Minimum Samples

Future gates should require minimum games, snaps, targets, carries, or opportunities by position. Small inside-10 and inside-5 samples must carry caveats.

## Injury, Bye, Team, And Position Handling

Injury and bye weeks must be explicit missingness/context, not silent zero-value labels. Team and position changes must preserve point-in-time identity and avoid future roster leakage.

## Rookies And Veterans

This NFL usage lane starts after NFL entry. CFBD/college evidence is a separate future lane.

## Contamination Blocks

No ADP, market, DynastyProcess, projections, rankings, vendor opinion values, current ranks, or target labels may appear as features.
