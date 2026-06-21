# API-SPORTS NFL & NCAA Source Evaluation - 2026-06-21

## Purpose

Evaluate API-SPORTS NFL & NCAA as a possible low-cost/free fallback source for
NWR, especially for the live 2026 injury/practice-status gap.

This is source discovery and policy only. No integration is approved.

## Master Verdict

YELLOW: potentially useful as a fallback/cross-check source, especially for
injuries and possibly NCAA/rookie context, but blocked from integration until
Tim/Master validates license terms, field quality, endpoint availability, and
free-tier feasibility with a key-backed local-only spike.

API-SPORTS should not replace:

- Sleeper as league truth.
- Sleeper as current primary ADP market/timing context.
- nflverse as the primary open factual NFL stats/backtest backbone.

## Sources Reviewed

- Official NFL & NCAA product page:
  `https://api-sports.io/sports/nfl`
- Official API-SPORTS terms:
  `https://api-sports.io/terms`
- Detailed documentation page:
  `https://api-sports.io/documentation/nfl/v1`

Note: the detailed documentation page was protected by a browser/Cloudflare
challenge in the local CLI check, so endpoint-specific conclusions below rely on
the official product page, Tim's described docs list, and future validation gates.

## Source Overview

| Area | Finding |
| --- | --- |
| Product | API-SPORTS NFL & NCAA / API-NFL & NCAA |
| Coverage advertised | NFL and NCAA USA |
| Product-page coverage categories | Schedule, historical data, events, team statistics, game player statistics, player statistics, injuries, standings, country |
| Product-page scale claims | 17 years of data, 18,406 games, 892 teams, 68,900 players |
| Authentication | API key/account required for API calls |
| Free plan | 100 requests/day; quota resets at 00:00 UTC |
| Paid plans shown | PRO: 7,500 requests/day, 300 requests/min, shown at 15.00 on one-month tab; ULTRA: 75,000/day at 25.00; MEGA: 150,000/day at 35.00 |
| Terms/licensing | YELLOW. Data obtained from partners; resale prohibited; API-SPORTS does not grant publication/commercial rights; users must verify required rights holder permissions. |

## Terms And Licensing Notes

API-SPORTS terms materially affect NWR use:

- Accounts are individual and cannot be shared or duplicated to increase free
  limits.
- The data is obtained from partners and direct resale is prohibited.
- API-SPORTS says it does not provide a license for publication/use of data in
  applications, websites, or products; required permissions must be obtained from
  competent authorities where applicable.
- Fantasy sports platforms or mass media distribution may require additional
  licenses from rights holders.
- Data is provided as-is, may contain errors, and update frequencies are not
  guaranteed.
- The free plan can be modified at any time and is limited in available data.

NWR implication: API-SPORTS can be evaluated for local/private display and
cross-check workflows, but cannot be promoted into production, public
distribution, final draft decisions, or model/private-value workflows without
source-policy approval and license review.

## Endpoint Fit Table

| Endpoint/feed | Advertised/use-case fit | NWR gap fit | Current recommendation | Status |
| --- | --- | --- | --- | --- |
| Injuries | Potential live/current injury feed | Could fill direct 2026 injury/practice gap if fields are current and include report/practice status | Test later with key-backed local-only schema spike | YELLOW helpful |
| Weekly Injuries | Potential weekly injury/practice status | Strongest possible fit for current NWR gap | Highest priority API-SPORTS validation target | YELLOW helpful |
| Weekly Depth Charts | Weekly/team depth position/order | Mostly redundant because nflverse `load_depth_charts(2026)` works, but useful cross-check | Fallback/cross-check only | YELLOW redundant/helpful |
| Team Roster | Current roster/player/team context | Redundant with Sleeper league truth and nflverse rosters | Fallback only | YELLOW redundant |
| Player Profile | Biographical player context | Redundant with nflverse players/rosters/ff_playerids | Fallback only | YELLOW redundant |
| Game Roster / inactive status | Game-day active/inactive context | Could help if it has official inactive/game roster timing | Test after injuries | YELLOW possible gap-fill |
| Daily Transactions | Adds roster movement evidence | Sleeper transactions cover league roster movement; NFL transactions could supplement real-world status | Display/cross-check only | YELLOW supplemental |
| Free Agents | Real-world FA status | Useful for dropped-veteran/team status notes, but not required for current pipeline | Optional cross-check | YELLOW supplemental |
| Game Statistics | Box score/game/player stats | Redundant with nflverse player/team stats and PBP | Avoid as primary; fallback only | YELLOW/low priority |
| Game Play-by-Play | Play-level events | Redundant/weaker than nflverse PBP unless API fields differ | Avoid for V0; no need before nflverse PBP derivations | YELLOW redundant |
| Seasonal Statistics | Season/player/team stats | Redundant with nflverse season/team/player stats | Avoid as primary | YELLOW redundant |
| Draft Summary / Prospects / Top Prospects | Draft/rookie/NCAA prospect context | Could supplement CollegeFootballData/Rookie HQ if fields are useful | Test later, not urgent | YELLOW optional |

## Comparison Against Current NWR Coverage

| NWR signal/gap | Current source | API-SPORTS value add | Recommendation |
| --- | --- | --- | --- |
| League rosters, ownership, draft order, transactions | Sleeper | Not a replacement | Do not use for league truth. |
| ADP/market timing | Sleeper ADP display context | No clear true-ADP advantage | Do not use for ADP unless Sleeper fails. |
| Weekly/player/team stats | nflverse | Mostly redundant | Keep nflverse primary. |
| Play-by-play/red-zone/team environment | nflverse PBP/team stats | Redundant unless fields are easier/cleaner | Use nflverse first. |
| Depth charts | nflverse `load_depth_charts(2026)` | Cross-check only | Optional fallback. |
| 2026 injuries/practice status | nflverse local runtime failed for 2026 injury feed | Material possible value | Primary reason to evaluate API-SPORTS. |
| Game-day inactive status | Not yet normalized in NWR | Possible value if endpoint exists and is timely | Secondary validation target. |
| NCAA/rookie data | CollegeFootballData planned; Rookie HQ manual board | Potential fallback | Optional source-gap research only. |
| Exact routes run / TPRR | Missing/unclear | Not advertised as direct | Do not assume it fills gap. |
| Direct OL grades | Missing/external | Not advertised as direct grades | Not a likely solution. |

## Free-Plan Feasibility

Free plan: 100 requests/day.

Likely feasible within free tier:

- Weekly injury refresh if a single endpoint can return all NFL weekly injuries
  by season/week.
- Weekly depth chart cross-check if a single endpoint can return league-wide
  weekly depth charts.
- Limited one-off validation for a few endpoints.
- Local-only source schema/spike work.

May need paid plan:

- Team-by-team endpoint design requiring 32+ requests per feed per week.
- Combining injuries, depth charts, game rosters, transactions, NCAA, and player
  profiles every day.
- Historical backfills.
- Broad game/play-by-play/stat refreshes.

Paid plans shown on the product page provide all endpoints/all competitions with
higher quotas. Before paying, Tim should confirm currency, billing period,
available historical range, account terms, and whether private local fantasy
research use is acceptable.

## NWR Policy Classification

| Use case | Classification | Reason |
| --- | --- | --- |
| Live 2026 injury/practice fallback | YELLOW test later | Most meaningful possible gap-fill. Needs key-backed field/timing validation. |
| Live depth chart fallback | YELLOW fallback only | nflverse already covers 2026 depth charts. |
| NCAA/rookie fallback | YELLOW optional | Could supplement CFBD/Rookie, but not urgent. |
| Display-only source cross-check | YELLOW acceptable after license/key validation | Good fit if not committed or used as private value. |
| Private value/model/ranking/recommendation/simulation/final decisions | RED blocked | License/source policy not approved; field quality unvalidated. |
| Primary NFL stats source | RED/not recommended | nflverse is stronger/open primary backbone. |

## Recommendation

Recommended status: fallback-only, test later.

API-SPORTS should be included in the Deep Research source-gap prompt as a
candidate for:

- live 2026 injury/practice status fallback
- game-day inactive status fallback
- depth chart cross-check
- NCAA/rookie data fallback if CFBD/Rookie needs remain

It should not block the first backtest. The first backtest can proceed with
nflverse/Sleeper/current NWR sources because API-SPORTS is mainly a live
injury/depth fallback and not a prerequisite for historical stat modeling.

## Exact Questions For Tim Before Any Integration

1. Is Tim willing to create an API-SPORTS account/API key for a local-only spike?
2. Does the free plan expose all NFL/NCAA endpoints needed for injuries and depth
   charts, or are fields/historical seasons restricted?
3. Are injury endpoints league-wide or team-by-team/week-by-week?
4. Do weekly injuries include report status, practice status, injury type, and
   timestamp/date modified?
5. Does game roster/inactive status exist and update before games?
6. Are terms acceptable for private/local fantasy research use?
7. Would any public/hosted display, if ever desired, require additional rights
   holder permission?
8. What currency/billing terms apply to the displayed paid-plan prices?

## Next Prompt If Approved Later

```text
You are Master/Main HQ for Niners War Room.

Run a local-only API-SPORTS NFL/NCAA schema validation spike using a Tim-provided
API key stored outside Git. Do not commit raw vendor data. Do not create Lane
Exchange packages. Test only injuries, weekly injuries, game roster/inactive
status, weekly depth charts, and source status/limits. Return endpoint field
schemas, row counts, timestamps, rate-limit usage, license notes, and whether
API-SPORTS can safely fill the 2026 injury/practice-status gap.
```

## Final Verdict

YELLOW.

API-SPORTS appears potentially useful as a low-cost/free fallback for the 2026
injury/practice-status gap and source cross-checking. It is not needed for the
first backtest and should not become private value, model training, rankings,
recommendations, simulations, final draft decisions, deployment, or production
data without later Tim/Master/QA approval.
