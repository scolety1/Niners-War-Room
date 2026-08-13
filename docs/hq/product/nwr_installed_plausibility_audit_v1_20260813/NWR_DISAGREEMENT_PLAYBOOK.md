# NWR disagreement playbook

This playbook describes how the installed 10-team 1QB Dynasty and profile-specific Redraft systems tend to disagree with generic public rankings. It is decision guidance, not a mandate to follow consensus.

## Magnitude bands

Use absolute overall-rank differences only when the format and player pool are reasonably compatible. The bands reflect materially different startup-round neighborhoods in a 240-player Dynasty pool:

| Band | Comparable rank difference | Owner meaning |
| --- | ---: | --- |
| Small | 0-9 | Normal analyst noise; no warning needed. |
| Moderate | 10-24 | Review if the player is central to a deal. |
| Large | 25-49 | NWR is making a meaningful independent call. |
| Extreme | 50+ | Inspect evidence freshness, format, role, and confidence before acting. |

Do not use the band when comparing Superflex to 1QB, TE-premium to non-premium, Redraft to Dynasty, or position rank to overall rank. For those cases, record a qualitative neighborhood only.

## How NWR tends to differ from consensus

### 1. Production and opportunity persistence

NWR will keep productive veterans and target earners materially higher than generic Dynasty markets. Sutton (#29), Davante Adams (#47), Christian McCaffrey (#18), and Jonathan Taylor (#4) are the clearest current examples. The internal evidence does show age and downside flags; the disagreement comes from the final balance, not from age being ignored.

Owner category: **DOUBLE-CHECK**. Verify current role, injury recovery, and whether the league rewards win-now points enough to justify the lifecycle risk.

### 2. Efficiency/talent before generic role certainty

Alec Pierce (#27), Jameson Williams (#26), Michael Wilson (#34), and Parker Washington (#44) show that NWR is willing to elevate explosive or efficient evidence even when public role confidence is lower. This is not a universal low-volume boost: inefficient/high-volume cases are not all promoted.

Owner category: **TRUST NWR MORE** as an independent shortlist signal; **DOUBLE-CHECK** snap share and target sustainability before paying the full rank.

### 3. Shallow 1QB replacement economics

The system can rank elite real-life quarterbacks very far apart and pushes many usable QBs into the overall tail. Purdy at #185/QB21 is the most visible case. This is intentional position economics, not an NFL-quality judgment.

Owner category: **DOUBLE-CHECK, BUT UNDERSTAND THE FORMAT THESIS**. The shallow-league direction is intentional, but exact Finished V1 historical calibration is unavailable. Check manager hoarding, bench depth, passing scoring, and whether the league is actually Superflex before acting on a tail rank.

### 4. Uneven elite-TE treatment

McBride #8 and Pitts #17 are far ahead of Bowers #45. Public 2026 Dynasty lists generally put Bowers in the top 12-23, often ahead of Pitts. This is the cleanest current relative-position outlier because format mismatch does not explain it.

Owner category: **DOUBLE-CHECK**. Inspect the individual research reasons and confirm that Bowers' role/health/team context is current.

### 5. Rookie evidence separation and fail-closed gates

Raw rookie score is not the final order. Draft capital, production, evidence completeness, identity resolution, and confidence caps can move or block a prospect. Love, Tate, and Concepcion are plausible after the 2026 draft. Stribling proves the cost of fail-closed governance: truthful `blocked` status can lag a real pick-33 event.

Owner category: **TRUST NWR MORE** for identifying missing evidence; **TRUST EXTERNAL CONTEXT MORE** for late draft/team news until ingestion catches up.

### 6. Refusal to price unknown future picks as known slots

The Trade Analyzer keeps pick-slot uncertainty explicit and will not manufacture an exact named counter without roster/pick-ownership context. This makes pick-heavy packages look conservative and keeps some labels at `COUNTER`.

Owner category: **TRUST NWR MORE** for honesty; manually supply league-specific pick probability and ownership context.

### 7. Coarse outcome calibration

Outcome probabilities repeat within position/tier families and remain properly bounded/nested. They are useful as calibrated bands and horizon context, not as bespoke single-decimal forecasts.

Owner category: **TRUST NWR MORE** for direction and horizon; **DOUBLE-CHECK** apparent precision.

### 8. Stale market gaps as research prompts

The July 17 market lens is intentionally display-only. Large positive gaps identify where to investigate but can be driven by missing current team/status/route evidence. Joe Mixon and several veteran depth receivers illustrate this.

Owner category: **TRUST EXTERNAL CONTEXT MORE** for current price; use NWR to ask why consensus may be overreacting.

## Where NWR appears strongest

- Applying 10-team 1QB replacement economics instead of importing Superflex scarcity.
- Showing evidence confidence, risk, and missing-data gates rather than silently imputing certainty.
- Separating team-window, youth, production, upside, pick-flexibility, and format-fit trade dimensions.
- Treating rookie review and veteran production as different evidence authorities.
- Using market gaps to surface research candidates without letting the market overwrite the model.

## Where NWR appears weakest

- Late-breaking injury, trade, depth-chart, and team-status information.
- Elite-TE relative ordering where the current Bowers/Pitts split is difficult to reconcile with public evidence.
- Trade synthesis now exposes its ordinal evidence units and decisive threshold; continue reading dimensions for cross-authority packages.
- Dynasty and Rookie outlook cards now use source-native signal labels; their values still are not a shared numeric scale.
- Any conclusion that depends on an optional, stale market artifact being identical across packaging contexts.

## Scenarios to double-check

- Extreme gap (50+) with low/capped confidence.
- Veteran ranked 25+ spots above public Dynasty consensus.
- Young cornerstone ranked 25+ spots below multiple compatible public lists.
- Quarterback value in leagues that do not behave like a shallow 10-team 1QB market.
- Trade where opposing clear dimensions keep the call at `COUNTER` even after the preferred side changes.
- Rookie whose real draft/team event occurred after the evidence snapshot.

## Current major independent calls

See `CURRENT_MAJOR_OUTLIERS.csv`. The highest-priority reviews are Bowers #45, Jeanty #46, Sutton #29, Pitts #17, Purdy #185 in 1QB, and stale-market positive gaps led by Joe Mixon.

## What to check manually before acting

1. Current injury/status and team.
2. Depth chart, snaps, routes, and expected workload.
3. League behavior: QB/TE hoarding, lineup depth, and scoring bonuses.
4. Whether a market/reference is 1QB, Superflex, TE-premium, PPR, or Redraft.
5. Rookie identity, draft capital, and post-draft role.
6. Future-pick ownership and probable slot range.
7. Whether an NWR confidence cap or blocked status is doing most of the work.

## Historical usefulness

No fair timestamped historical forecast/consensus outcome panel was available in this audit. Every archetype is therefore marked `NOT_ENOUGH_INFORMATION` rather than retroactively labeling it helpful or harmful.
