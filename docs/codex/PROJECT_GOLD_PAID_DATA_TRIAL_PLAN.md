# Project Gold Paid Data Trial Plan

Last reviewed: 2026-05-14

This plan prepares a controlled paid-data trial for the Niners War Room without buying,
scraping, or wiring paid data into formulas. The goal is to test whether a paid or premium
source can reduce the current review-only source gaps: true route participation, route
share, targets per route run, YPRR, expected opportunity, stable projections, injury
context, and reliable player IDs.

Rankings must remain review-only until trial data is legally exported, mapped, validated,
receipted, and passed through sanity gates.

## Provider Checklist

| provider | likely best use | route/run data | projections | injury/depth | ids/export/API | evidence confidence | trial verdict |
|---|---|---:|---:|---:|---:|---:|---|
| Fantasy Points Data Suite | routes, route share, target share, YPRR, red-zone/role research | likely strong | unclear | unclear | verify export/API | 80 | highest priority for route/usage trial |
| SportsDataIO | API depth, injuries, red-zone/third-down, projections, IDs | unclear | yes | strong | strong API | 85 | highest priority for API trial |
| FantasyData | lower-cost API/data dictionary plus CSV/XLS web exports | likely useful | yes | good | API + visible CSV/XLS tables | 80 | useful budget/API trial |
| FantasyPros | projections and consensus/rank context | no | yes | limited | public API access request | 70 | projection-only trial |
| PFF+ | routes run, YPRR, advanced receiver/RB/TE metrics | strong | no/limited | limited | premium CSV export, API unclear | 80 | highest priority for route/YPRR CSV trial |

## Detailed Provider Matrix

| field / capability | Fantasy Points Data Suite | SportsDataIO | FantasyData | FantasyPros | PFF+ |
|---|---|---|---|---|---|
| routes run | appears available via Data Suite tools; verify export | not confirmed in public NFL API pages | advanced metric tables show routes run for pass catchers; verify export depth | no | yes, PFF premium stats/articles reference routes and YPRR |
| route share | appears available in Data Suite examples; verify export | not confirmed | not confirmed | no | likely derivable if routes/dropbacks available; verify export |
| snap share | likely available or adjacent; verify | depth and player feeds exist; exact snap field requires trial | yes, snap-count tables include snap % | no | likely available; verify export |
| target share | appears available in Data Suite examples | fantasy metrics/red zone/third-down context; exact field requires trial | visible snap/target share tables | no direct route stat; projections include targets only | likely available through premium receiving data; verify export |
| targets per route run | likely available or derivable if routes + targets export | not confirmed | not confirmed | no | derivable from routes + targets; verify export |
| YPRR | Data Suite examples mention YPRR | not confirmed | advanced WR/TE/TE examples show yards/targets/route-style fields; verify exact export | no | yes, PFF premium stats include yards per route run |
| RB weighted opportunities | derive from carries/targets/red-zone fields if exported | derive from stats + red-zone feeds | derive from stats/snap/red-zone exports | partial projection-only | derive manually if carries/targets/routes available |
| red-zone / goal-line role | Data Suite likely has red-zone tools; verify export | yes, red-zone and third-down stats advertised | yes, red-zone stats visible | no | likely charting/situational stats; verify |
| projections | unclear | yes, weekly/season/fantasy projections advertised | yes, PlayerGameProjection documented | yes, API projections endpoint | not primary |
| injuries | unclear | yes, injury feeds and workflow docs | yes, status/injury fields documented | player news/status limited | not primary |
| depth charts | unclear | yes, depth chart endpoints | yes, depth charts visible | no | not primary |
| player IDs | verify | strong SportsDataIO PlayerID; mapping required to Sleeper/nflverse | FantasyData/SportsDataIO PlayerID; mapping required | FantasyPros FPID; mapping required | PFF ID/name mapping; mapping required |
| CSV/export/API access | verify whether Data Suite exports CSV | API, JSON/XML; commercial terms | API/data dictionary; web tables show CSV/XLS in some views | public API by request for non-commercial use | CSV export cited for premium stats; API unclear |
| legal/local export fit | unknown until trial | good if API terms allow personal local cache | good if plan/API terms allow personal local cache | good if API key approved and terms followed | good for manual CSV export if subscription terms allow |
| main risk | export/API availability unknown | cost and field-package fit | may lack route/YPRR or full advanced fields | projections only, not route/usage | manual export friction and no clear API |

## Source Notes

- SportsDataIO advertises NFL feeds covering rosters/depth charts, injuries, weekly
  fantasy projections, fantasy stats, and player stats. Its workflow guide describes
  depth-chart endpoints, injury/depth handling, player details, draft metadata, and
  weekly/season-long projection timing.
- FantasyData's data dictionary documents PlayerGameProjection and player/status fields,
  and its visible fantasy pages expose snap-count, target-share, red-zone, depth-chart, and
  player-stat style tables. FantasyData appears tied to SportsDataIO/Discovery Lab, so treat
  it as a lower-cost API trial candidate rather than a separate premium route-data source.
- FantasyPros has a documented public API request path for personal non-commercial API
  keys and a projections endpoint with standard/PPR/half scoring parameters. It is a
  projection source, not a route/usage source.
- PFF publicly describes Premium Stats as covering seasons back to 2006, yards per route
  run, player-level advanced stats, and CSV export for premium fantasy/signature stats.
  It is a likely strong manual-export test for routes/YPRR, but not a clean API-first path.
- Fantasy Points Data Suite pages and articles show Data Suite route/run style tools and
  examples including route share, target share, and YPRR. Public pages do not clearly prove
  API or CSV export; the trial must verify export before relying on it.

## Trial Checklist

Run this checklist before any provider is allowed to affect model outputs.

| check | required evidence | pass/fail rule |
|---|---|---|
| Terms reviewed | link or saved copy of provider terms/API agreement | fail if local personal export/API use is unclear |
| Export method | CSV/XLS export button, documented API, or written permission | fail if it requires scraping rendered pages |
| Sample size | 20-30 named players from the trial sample | fail if the sample cannot cover all core positions |
| Stable fields | two exports/pulls with matching field names | fail if provider fields drift without documentation |
| ID mapping | provider ID/name mapped to Sleeper plus nflverse/GSIS/PFR where possible | fail if any high-value ambiguous identity remains |
| Critical-bucket gain | coverage diff proves role/usage, projection, injury, or identity improved | fail if it only duplicates free data |
| Receipt display | raw fields can appear in player receipts with source date and warning status | fail if fields cannot be audited by player |
| Model isolation | output stored under `local_exports/paid_data_trials/...` only | fail if trial rows mutate active model outputs |

## Trial Sample

Use 30 players so the trial covers the exact model failure modes without overbuilding an
integration:

Post-Pro update: the current paid-data trial contract now uses a full 40-player Truth Set,
with a required 20-player minimum subset if provider limits are tight. The concrete sample
CSV is saved at
`templates/real_data_inputs/paid_data_trial/paid_data_trial_sample_players.csv`.

| group | players | purpose |
|---|---|---|
| Niners roster core | Lamar Jackson, Brian Thomas, De'Von Achane, Luther Burden, Kaleb Johnson, Jayden Higgins | roster-decision and young-bridge audit |
| disputed comparisons | Jaxon Smith-Njigba, Tee Higgins, Chase Brown, Brenton Strange, Kyren Williams, Bijan Robinson, Jahmyr Gibbs | known weirdness and RB/WR balance |
| elite anchors | Ja'Marr Chase, Justin Jefferson, CeeDee Lamb, Amon-Ra St. Brown, Puka Nacua, Malik Nabers, Brock Bowers | top-tier calibration |
| role/snap tests | Christian McCaffrey, James Cook, Josh Jacobs, Brian Robinson, Jerry Jeudy, Brandon Aiyuk, David Montgomery, Romeo Doubs | snap/role and age/injury checks |
| QB/TE suppression | Josh Allen, Jalen Hurts, Patrick Mahomes, Trey McBride, George Kittle | 1QB and no-TE-premium behavior |

If a provider has request limits, use the first 20 players from the table and keep the
same schema.

## Trial Import CSV Contract

Do not plug these rows into formulas directly. Store them under
`local_exports/paid_data_trials/<provider>/<trial_id>/`.

Minimum trial file:

```text
provider,trial_id,exported_at,source_terms_checked,player_name,position,nfl_team,
provider_player_id,sleeper_id,gsis_id,pfr_id,season,week_or_scope,
routes_run,route_share,snap_share,target_share,targets_per_route_run,yprr,
rb_weighted_opportunities,red_zone_opportunities,goal_line_opportunities,
projected_games,projected_passing_yards,projected_passing_tds,projected_interceptions,
projected_rushing_attempts,projected_rushing_yards,projected_rushing_tds,
projected_targets,projected_receptions,projected_receiving_yards,projected_receiving_tds,
injury_status,practice_status,depth_chart_position,depth_chart_rank,
raw_export_file,field_notes
```

Provider-specific gaps should stay blank, not estimated.

## Post-Pro Trial Templates

Use these templates before requesting or importing any paid sample:

- `templates/real_data_inputs/paid_data_trial/paid_data_trial_sample_players.csv`
- `templates/real_data_inputs/paid_data_trial/paid_data_trial_required_fields.csv`
- `templates/real_data_inputs/paid_data_trial/paid_data_trial_provider_comparison.csv`
- `templates/real_data_inputs/paid_data_trial/paid_data_trial_acceptance_criteria.csv`

The phase-specific criteria note is saved at
`docs/codex/POST_PRO_AUDIT_PHASE_6_PAID_DATA_TRIAL_CRITERIA.md`.

## Acceptance Criteria

A provider passes the paid-data trial only if all of these are true:

1. **Legal local export**: terms allow personal/non-commercial local analysis or an API
   key explicitly allows this use.
2. **No forbidden scraping**: browser-only paid pages are acceptable only if the site has a
   supported CSV/export button or written permission.
3. **Stable fields**: exported file/API has stable field names across at least two pulls.
4. **Reliable ID mapping**: 95%+ of sample players map to Sleeper/nflverse/GSIS/PFR with
   no ambiguous high-value players.
5. **Critical-bucket improvement**: trial data fills or upgrades at least one current
   critical bucket: production, role/usage, age/bio, or identity. Best paid target is
   role/usage because current free data leaves it proxy-heavy.
6. **Receipt compatibility**: every imported field can be shown in player receipts with
   raw value, normalized value, source, source date, and warning status.
7. **Model isolation**: paid data remains preview-only until the model audit packet shows
   improved coverage and sanity fixtures pass.

## Trial Order

1. **Fantasy Points Data Suite or PFF+ route/YPRR export test**
   - Purpose: attack the role/usage and receiving-efficiency problem directly.
   - Pass condition: can export routes run, route share or route proxy, target share, TPRR,
     and YPRR for the sample set.
   - Fail condition: no legal local export/API, or player IDs are too hard to map.

2. **FantasyPros projections API request**
   - Purpose: fill optional projections with a clean legal API.
   - Pass condition: API key approved; projection fields include enough volume stats to
     rescore into LVE. First downs may be estimated with visible penalty.
   - Fail condition: no access, terms conflict, or fields are too shallow.

3. **SportsDataIO / FantasyData API trial**
   - Purpose: test paid API reliability for injuries, depth charts, snap counts, red-zone,
     projections, and player IDs.
   - Pass condition: one API can replace multiple brittle/manual imports.
   - Fail condition: route/YPRR is unavailable and cost is high for only fields nflverse
     already covers.

4. **Market/liquidity source**
   - Purpose: optional trade edge only.
   - Pass condition: legal export with player IDs and transparent scoring context.
   - Fail condition: anything that would tempt the private model away from stats-first.

## Provider Decision Rubric

| score area | weight | pass signal |
|---|---:|---|
| role/route data quality | 30 | routes, route share, TPRR, YPRR available and exportable |
| projection quality/export | 20 | legal API/export and LVE-rescoreable stat categories |
| ID mapping | 20 | stable provider IDs plus Sleeper/nflverse/PFR bridge |
| legal/local workflow | 15 | no scraping, clear local export/API terms |
| cost-to-edge | 10 | fills critical gaps that free data cannot |
| UI/receipt fit | 5 | raw fields can be displayed cleanly in receipts |

Minimum score to continue beyond trial: 80/100.

## Trial Decision Log Template

Append one row per provider trial.

```text
provider,tested_at,sample_player_count,legal_export,export_method,id_match_rate,
critical_bucket_improvement,fields_missing,terms_risk,cost_estimate,
recommendation,next_action,reviewer
```

Recommended decisions:

- `reject`: terms, fields, mapping, or cost-to-edge do not justify more work.
- `keep_testing`: useful fields exist, but sample/mapping/terms need one more pass.
- `candidate_subscription`: provider clearly fills critical gaps and passes export rules.
- `defer`: source is useful later but not needed before roster decisions.

## What Not To Do Yet

- Do not subscribe before confirming export/API terms.
- Do not scrape paid pages.
- Do not let projections or market data overwrite private/stat value.
- Do not merge paid source fields into formulas during the trial.
- Do not mark the app decision-ready because a paid source looks promising.

## References

- [SportsDataIO NFL API](https://sportsdata.io/nfl-api)
- [SportsDataIO NFL workflow guide](https://sportsdata.io/developers/workflow-guide/nfl)
- [SportsDataIO fantasy sports API](https://sportsdata.io/fantasy-sports-api)
- [FantasyData NFL data dictionary](https://developers.fantasydata.com/data-dictionary/nfl)
- [FantasyData NFL snap counts](https://fantasydata.com/nfl/nfl-snap-counts)
- [FantasyPros API access request](https://support.fantasypros.com/hc/en-us/articles/49749297704475-How-do-I-request-access-to-the-FantasyPros-API)
- [FantasyPros API reference](https://api.fantasypros.com/v2/docs)
- [PFF Premium Stats overview](https://www.pff.com/news/pro-pff-premium-stats-highlighting-all-of-pffs-advanced-metrics-and-grades)
- [PFF fantasy export article](https://www.pff.com/news/fantasy-football-how-to-get-the-most-out-of-a-pff-subscription-for-fantasy)
- [Fantasy Points Data Suite routes tool](https://data.fantasypoints.com/nfl/tools/player/receiving-routes-run)
- [Fantasy Points Data Suite tools article](https://www.fantasypoints.com/nfl/articles/2024/fantasy-points-data-suite-new-tools)
