# Project Gold Sprint 3 / Phase 18: Source Quality Upgrade Trial

Last reviewed: 2026-05-14

This is a source-quality recommendation for Niners War Room. It does not implement paid
data, scrape paid pages, tune formulas, or unlock decision-ready status.

Current rankings remain review-only.

## Bottom Line

Free/public data is good enough to keep working through pre-declaration roster decisions
as an audited review tool, but it is not yet good enough to call the model final.

The biggest data weakness is **not** age, identity, or league-rank data. Those are mostly
working for the Niners roster. The biggest weakness is **true route/participation and
role-quality data**:

- 24 of 24 Niners players still carry `missing_participation_proxy`.
- `route_role` is neutral/default-like for the Niners roster.
- 20 of 24 Niners players use `local_baseline_projection`, not independent projections.
- 20 of 24 Niners players still show `stale_lve_scoring_source`.
- 3 Niners players have `no_injury_report_rows`.

That means a paid-data trial is worth considering, but only as a controlled sample. The
best first test is a **route/usage export**, not a generic rankings or market subscription.

Recommended first trial:

**Fantasy Points Data Suite route/usage export**, if legal local export/API access is
confirmed. If that cannot export cleanly, use **PFF+ premium CSV export** as the route/YPRR
fallback.

API fallback:

Use **FantasyData** first if budget matters and it fills projections/injuries/snap/depth
fields. Use **SportsDataIO** first only if API reliability and supported workflow matter
more than cost.

Do not use FantasyPros, consensus ranks, or market data as a private-value fix. Those can
help projection sanity or trade liquidity later, but they do not solve the stats-first
problem.

## Audit Exports

Export folder:

`local_exports/model_audits/sprint3_phase18_source_quality_upgrade_trial_20260514`

Files:

| file | purpose |
|---|---|
| `manifest.json` | active pack, active source root, review-only status, and row counts |
| `niners_source_quality_gaps.csv` | player-level Niners roster source gaps from normalized feature rows |
| `source_quality_trial_recommendations.csv` | gap-by-gap free/paid recommendation matrix |

Manifest highlights:

| check | value |
|---|---:|
| Niners roster players | 24 |
| Niners matched to normalized features | 24 |
| local baseline projections | 20 |
| missing projections | 4 |
| missing participation proxy warnings | 24 |
| stale LVE scoring source warnings | 20 |
| source gap acceptance rows | 15 |

## Niners-Impacting Gaps

| gap | Niners affected | free/public fill? | paid trial? | decision impact |
|---|---:|---|---|---|
| route/participation | 24 | partial only | yes | Highest risk. This can distort WR/TE target earning, RB receiving role, and role security. |
| independent projections | 24 | weak | maybe | Optional for roster decisions, important for final draft confidence. |
| production freshness | 20 | yes | no first | Fix nflverse/public import before paying. |
| injury/practice context | 3 direct missing rows | partial | later | Useful closer to declaration deadline, but not the first paid priority. |
| age/bio | 0 Niners blocked | yes | no | Current Niners rows use derived real age data. |
| identity | 0 Niners unmatched | yes | no | Current Niners roster matches normalized feature rows. |
| market/liquidity | all missing/defaulted | optional | later | Trade context only; cannot fix private football value. |

## Free/Public Data Verdict

Free/public data can carry these buckets:

| bucket | verdict | notes |
|---|---|---|
| identity | enough | Sleeper plus nflverse/DynastyProcess-style IDs are the right backbone. |
| age/bio | enough | Current Niners rows are derived real data. |
| historical production | should be enough | If still stale, fix import/as-of metadata before buying data. |
| first-down scoring | should be enough | nflverse/play-by-play-derived first downs should support LVE scoring. |
| basic injury availability | partial | Public injury feeds are useful but incomplete in offseason windows. |
| role/security | partial | Snap/depth/weekly stats help, but route participation is still weak. |
| projections | weak | Local baselines must stay quarantined as non-independent evidence. |
| market/liquidity | optional | Useful for trade edge only, not private value. |

## Paid Trial Recommendation

### Best First Trial: Fantasy Points Data Suite

Trial purpose: fill the role/usage gap with actual route and target-earning evidence.

Fields to test:

- routes run
- route share
- snap share
- target share
- targets per route run
- yards per route run
- red-zone routes or red-zone targets
- goal-line opportunities for RBs
- provider player ID, player name, position, NFL team
- source date and season/week scope

Why this is first:

Fantasy Points publicly shows Data Suite route/usage tools, including receiving routes
run and examples involving route share, target share, and YPRR. Those are directly tied to
the current `missing_participation_proxy` weakness.

Trial risk:

Public pages do not prove that the data can be legally exported to local CSV/API. This
must be verified before relying on it.

### Best Fallback: PFF+

Trial purpose: manual CSV route/YPRR export if Fantasy Points cannot export cleanly.

Fields to test:

- routes run
- YPRR
- target/receiving usage fields if available
- snap/position usage fields if available

Why this is fallback:

PFF publicly describes Premium Stats and fantasy/signature-stat CSV export, and PFF
materials reference YPRR and advanced metrics. The concern is workflow friction and
whether the export is broad enough for local deterministic receipts.

### API Fallback: FantasyData or SportsDataIO

Use this if the priority becomes stable API feeds for projections, injuries, depth charts,
IDs, and snap counts.

FantasyData looks more budget/API-trial friendly. SportsDataIO looks more complete and
workflow-supported but may be expensive for this use case. SportsDataIO documents NFL
feeds for depth charts, injuries, projections, player stats, snap counts, red-zone and
third-down stats, and fantasy stats. FantasyData documents NFL projection and injury
fields through its data dictionary and related API ecosystem.

## Trial Sample

Use a 30-player sample. That is large enough to test every failure mode without turning
the trial into a full integration.

Sample groups:

| group | players |
|---|---|
| Niners roster decisions | Lamar Jackson, Brian Thomas Jr., De'Von Achane, Luther Burden, Kaleb Johnson, Jayden Higgins, Brenton Strange |
| Current roster role checks | Jerry Jeudy, Brandon Aiyuk, David Montgomery, Jakobi Meyers, Chase Brown, Ricky Pearsall |
| Disputed ranking anchors | Jaxon Smith-Njigba, Tee Higgins, Kyren Williams, Bijan Robinson, Jahmyr Gibbs |
| Elite WR anchors | Justin Jefferson, Ja'Marr Chase, CeeDee Lamb, Amon-Ra St. Brown, Puka Nacua |
| QB/TE suppression checks | Josh Allen, Jalen Hurts, Patrick Mahomes, Trey McBride, George Kittle |
| Additional RB/WR role checks | James Cook, Josh Jacobs, Christian McCaffrey, Romeo Doubs |

If provider limits force a smaller sample, start with the Niners roster decisions plus the
disputed ranking anchors.

## Acceptance Criteria

A paid source passes only if every item below is true:

1. Legal local export/API is confirmed.
2. No forbidden scraping is required.
3. Field names remain stable across at least two pulls/exports.
4. At least 95% of sample players match Sleeper/nflverse/PFR identity with no high-value
   ambiguous matches.
5. Route/usage coverage improves for at least 20 of 30 sample players.
6. New fields can be shown in receipts with raw value, normalized value, source, source
   date, warning status, and imputed flag.
7. Trial rows remain under `local_exports/paid_data_trials/...`.
8. Active model outputs do not change until explicit apply plus sanity fixture pass.

Fail conditions:

- Browser-only paid dashboard with no supported export.
- Export cannot be mapped to Sleeper/nflverse identities.
- Provider mostly duplicates free/public production data.
- Provider only offers rankings, ADP, or market values.
- Terms do not allow local analysis/export.

## What To Do Next

1. Fix free/public production freshness first. `stale_lve_scoring_source` should be solved
   by the nflverse pipeline before buying data.
2. Keep projection baselines quarantined. Local baseline projection is not independent
   forecast evidence.
3. Run a narrow route/usage paid trial only if you are willing to test export terms and a
   30-player sample.
4. Do not pay for market data yet. Market can create trade edge, but it should not rescue
   private rankings.
5. Keep rankings review-only until route/usage truth, production freshness, and sanity
   receipts pass the gate.

## Recommendation

| decision | value |
|---|---|
| free data enough for roster review? | yes, as review-only with receipts |
| free data enough for final model trust? | not yet |
| paid data worth testing? | yes, narrowly |
| best first trial | Fantasy Points Data Suite route/usage export |
| best fallback | PFF+ route/YPRR CSV export |
| best API fallback | FantasyData for budget; SportsDataIO for supported depth/injury/projection workflow |
| do not buy first | market/rank subscriptions |
| biggest expected edge | replacing `missing_participation_proxy` with real routes, route share, TPRR, and YPRR |

## References

- [Fantasy Points Data Suite routes tool](https://data.fantasypoints.com/nfl/tools/player/receiving-routes-run)
- [Fantasy Points Data Suite tools article](https://www.fantasypoints.com/nfl/articles/2024/fantasy-points-data-suite-new-tools)
- [PFF premium fantasy export article](https://www.pff.com/news/fantasy-football-how-to-get-the-most-out-of-a-pff-subscription-for-fantasy)
- [PFF Premium Stats overview](https://www.pff.com/news/pro-pff-premium-stats-highlighting-all-of-pffs-advanced-metrics-and-grades)
- [SportsDataIO NFL API](https://sportsdata.io/nfl-api)
- [SportsDataIO NFL workflow guide](https://sportsdata.io/developers/workflow-guide/nfl)
- [FantasyData NFL data dictionary](https://developers.fantasydata.com/data-dictionary/nfl)
- [FantasyData NFL snap counts](https://fantasydata.com/nfl/nfl-snap-counts)
- [FantasyPros API access request](https://support.fantasypros.com/hc/en-us/articles/49749297704475-How-do-I-request-access-to-the-FantasyPros-API)
- [FantasyPros API reference](https://api.fantasypros.com/v2/docs)
