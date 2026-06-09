# Project Gold Paid Data Value Assessment

Last reviewed: 2026-05-14

This audit decides whether paid data is worth using for Niners War Room. It does not
purchase anything, scrape anything, implement provider code, or wire paid source fields
into formulas.

Current rankings remain review-only.

## Bottom Line

Paid data is worth testing, but only for narrow gaps. It should not become a shortcut for
trusting the model.

The best first trial is a route/usage source: **Fantasy Points Data Suite first if legal
CSV/API export exists; PFF+ as the manual-export fallback**. The reason is simple:
current model weirdness is most likely to come from weak role, route, target-earning, and
young-player evidence. Those are exactly the areas free/public data cannot fully solve.

The second-best fallback is an API provider: **SportsDataIO or FantasyData**. Use these if
the first route-data trial fails export/legal checks, or if the main need becomes stable
projections, injuries, depth charts, and provider IDs.

Do not make **FantasyPros** the first paid trial. It can help projection or market context,
but it does not solve the model's most important statistics-first gaps.

## Current Model Gaps

Latest local report:

`local_exports/model_audits/free_data_gap_report_20260514_081239`

| bucket | class | active status | players | current problem | paid-data relevance |
|---|---|---:|---:|---|---|
| identity | critical | ready | 232 | mostly solved | paid provider IDs can help, but not worth buying for this alone |
| league rank | governance | ready | 232 | solved for current pack | no paid value |
| production | critical | review | 232 | active rows still look imputed/review-only | fix free nflverse pipeline first; paid data is not the right first answer |
| age/bio | critical | review | 232 | active rows still look imputed/review-only | fix free/nflverse ID + player metadata pipeline first |
| role/usage | critical | review | 232 | proxy-heavy, no true route/participation confidence | strongest paid-data target |
| projections | review | missing/review | 232 | no independent projection layer | useful paid target, but optional for roster decisions if labeled |
| injury | review | mostly ready | 219 ready / 13 review | rookies/young players often missing current context | paid data useful only near final roster/draft deadline |
| market/liquidity | review | missing | 232 | no external market anchor | useful for trade edge only, never private value |

The report lists **696 critical player-feature gaps** blocking decision-ready. However,
that does not mean "buy a provider and everything is fixed." Production and age/bio should
be solved by free/public imports. Paid data should target the areas that free data cannot
fully supply: **true role/usage, route participation, target earning per route, expected
opportunity, projections, and optionally injuries/depth charts.**

## Provider Ranking By Model Value

Scores are trial-priority scores, not source-quality guarantees. A provider can only pass
after a real 20-30 player local export/API sample.

| rank | provider | model value score | best use | biggest edge | main risk | recommendation |
|---:|---|---:|---|---|---|---|
| 1 | Fantasy Points Data Suite | 87 | route share, target share, YPRR, snap/route-style tools, role research | directly attacks role/usage and receiving profile gaps | export/API rights must be verified | best first trial |
| 2 | PFF+ | 83 | routes run, YPRR, snap/advanced player metrics, premium CSV export | strong route/YPRR evidence for WR/TE/RB pass-game roles | API unclear; may be manual CSV friction | best fallback if Fantasy Points export is weak |
| 3 | FantasyData | 78 | API/tables for snap counts, target share, red zone, projections, depth charts, player IDs | budget-friendly broad coverage and visible CSV/XLS style pages | exact route/TPRR/YPRR depth uncertain | best budget/API fallback |
| 4 | SportsDataIO | 76 | stable API for projections, injuries, depth charts, player details, IDs | enterprise-style API and strong workflow docs | cost may be high if it lacks true route data | best if API reliability matters more than routes |
| 5 | FantasyPros | 55 | projections, consensus/rank context, news/status | useful projection sanity layer | not stats-first route/usage; terms and scoring mismatch | projection-only, not core model |

## Scored Provider Matrix

| provider | role/usage coverage | projection quality | injury quality | export/API usability | ID mapping feasibility | cost/benefit | total | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Fantasy Points Data Suite | 30/30 | 6/15 | 4/10 | 12/20 | 8/10 | 27/30 | 87 | Highest value if export is real and legal |
| PFF+ | 29/30 | 2/15 | 3/10 | 11/20 | 8/10 | 30/30 | 83 | Great route/YPRR manual-export candidate |
| FantasyData | 18/30 | 13/15 | 8/10 | 17/20 | 9/10 | 13/30 | 78 | Best broad budget/API trial if route source fails |
| SportsDataIO | 14/30 | 15/15 | 10/10 | 20/20 | 10/10 | 7/30 | 76 | Great API, but likely too expensive unless it fills multiple gaps |
| FantasyPros | 2/30 | 14/15 | 3/10 | 13/20 | 7/10 | 16/30 | 55 | Useful only as projection/market context |

Weights behind the score:

- Role/usage coverage: 30
- Projection quality: 15
- Injury quality: 10
- Export/API usability: 20
- ID mapping feasibility: 10
- Cost/benefit: 30

Role/usage and cost/benefit are intentionally heavy because the model's biggest failure
mode is not "we need more opinion." It is "we need better evidence for how players are
actually used."

## Biggest Edge Fields

These fields would create the biggest improvement in the current model.

| priority | field | why it matters | likely best providers | model bucket |
|---:|---|---|---|---|
| 1 | routes run | separates actual pass-game role from box-score noise | Fantasy Points, PFF+ | role/usage |
| 2 | route share | tells whether WR/TE is actually earning full-time deployment | Fantasy Points, PFF+ | role/usage |
| 3 | targets per route run | separates target earning from just being on the field | Fantasy Points, PFF+ | target earning |
| 4 | YPRR | strong receiving efficiency input when paired with routes | Fantasy Points, PFF+, FantasyData if export confirms | efficiency |
| 5 | target share | stable enough to support WR/TE role and production expectations | Fantasy Points, FantasyData, PFF+ | role/opportunity |
| 6 | RB weighted opportunities | better than raw carries for role quality | Fantasy Points if available, derive from FantasyData/SportsDataIO | opportunity |
| 7 | red-zone / goal-line role | matters in no-PPR and first-down scoring | Fantasy Points, FantasyData, SportsDataIO | first-down/TD fit |
| 8 | season-long projections | fills forward-looking value, but must be rescored into LVE | SportsDataIO, FantasyData, FantasyPros | projection |
| 9 | current injuries / practice status | confidence and risk, especially near declaration deadline | SportsDataIO, FantasyData | injury |
| 10 | depth chart role | weak tiebreaker, useful only with warnings | SportsDataIO, FantasyData | role confidence |

## Fields That Are Not Worth Paying For First

| field/source type | why not first |
|---|---|
| Generic dynasty ranks | They mostly measure crowd opinion and format-mismatched liquidity, not LVE private value. |
| Market values | Useful for trade edge only; they should not fix private rankings. |
| Basic box-score production | nflverse/free public data should handle this. If production is still review-only, fix the import pipeline. |
| Age/bio/draft year | Free player-ID sources should handle this. Paid provider IDs can help but should not be the reason to subscribe. |
| Editorial blurbs/news | Helpful context, but not a deterministic model backbone. |
| Unofficial depth charts alone | They are too soft to drive role without snap/routes/target evidence. |

## Recommended First Trial

### Trial A: Fantasy Points Data Suite route/usage export

Purpose: determine whether it can legally export the route/usage fields that would most
improve the model.

Required sample fields:

- routes run
- route share
- snap share
- target share
- targets per route run or enough fields to derive it
- YPRR
- red-zone routes or red-zone targets
- goal-line carries/touches if available
- player name, position, NFL team, season/week

Pass conditions:

- Legal local export/API confirmed.
- At least 20 of 30 sample players export cleanly.
- At least 95% ID match rate against Sleeper/nflverse/PFR by exact ID or name+team+position review.
- Field names are stable across two exports.
- Coverage diff improves role/usage for the sample set.

Failure conditions:

- No legal local export.
- Only visual dashboard access with no supported export.
- Fields are too aggregated to audit by player/week.
- Player identity matching is manual for too many high-value players.

## Second-Best Fallback

### Trial B: PFF+ route/YPRR CSV export

Use this if Fantasy Points cannot export cleanly. PFF+ is attractive because public PFF
materials explicitly describe Premium Stats, YPRR, and CSV export for premium fantasy and
signature stats. The drawback is workflow friction: this may be manual CSV export rather
than a clean API.

Pass/fail conditions are the same as Trial A.

## API Fallback

### Trial C: FantasyData or SportsDataIO API sample

Use this if the goal shifts from route specificity to reliable API coverage.

Best fields:

- season-long projections
- weekly projections
- injuries / practice status
- depth charts
- snap counts / snap share
- target share / targets
- red-zone stats
- player IDs

Choose **FantasyData first** if budget matters and its fields cover enough sample needs.
Choose **SportsDataIO first** if API stability, injury/depth workflow, and official support
matter more than cost.

## Sources To Avoid For Core Value

| source | avoid as core because | allowed use |
|---|---|---|
| FantasyPros rankings/ECR | format-mismatched opinion layer, not LVE statistics | projection sanity or market/liquidity context only |
| Any scraped paid page | terms and reproducibility risk | never |
| Any provider without stable local export/API | cannot support deterministic receipts | manual read-only research only |
| Generic dynasty calculators | crowd liquidity, not private no-PPR first-down value | trade edge only |

## Cost/Benefit Recommendation

Do **not** buy a broad expensive API package before proving a route/usage source can fix
the actual ranking weirdness.

Best spend sequence:

1. Test one route/usage export source: Fantasy Points Data Suite or PFF+.
2. If route/usage test passes, import only into `local_exports/paid_data_trials/...` and
   compare receipts for the 30-player sample.
3. If rankings still look broken after route/usage fields are clean, then test a projection
   API from FantasyData/SportsDataIO/FantasyPros.
4. Only consider an API subscription if it replaces multiple brittle inputs at once:
   projections, injuries, depth charts, IDs, and red-zone context.
5. Do not pay for market data until the private model is trustworthy.

## Decision

Paid data is worth a controlled trial, not a subscription commitment.

Recommended status:

| decision | value |
|---|---|
| best first trial | Fantasy Points Data Suite route/usage export |
| best fallback | PFF+ route/YPRR CSV export |
| best API fallback | FantasyData first for budget, SportsDataIO first for enterprise stability |
| avoid as core model | FantasyPros ranks/ECR, generic market feeds, scraped paid pages |
| biggest edge fields | routes run, route share, TPRR, YPRR, target share, RB weighted opportunities, red-zone role |
| model status | review-only |

## References

- [Project Gold paid data trial plan](PROJECT_GOLD_PAID_DATA_TRIAL_PLAN.md)
- [Free data gap report manifest](../../local_exports/model_audits/free_data_gap_report_20260514_081239/manifest.json)
- [SportsDataIO NFL API](https://sportsdata.io/nfl-api)
- [SportsDataIO NFL workflow guide](https://sportsdata.io/developers/workflow-guide/nfl)
- [FantasyData NFL data dictionary](https://developers.fantasydata.com/data-dictionary/nfl)
- [FantasyData NFL snap counts](https://fantasydata.com/nfl/nfl-snap-counts)
- [FantasyPros API access request](https://support.fantasypros.com/hc/en-us/articles/49749297704475-How-do-I-request-access-to-the-FantasyPros-API)
- [FantasyPros API reference](https://api.fantasypros.com/v2/docs)
- [PFF Premium Stats overview](https://www.pff.com/news/pro-pff-premium-stats-highlighting-all-of-pffs-advanced-metrics-and-grades)
- [PFF fantasy export article](https://www.pff.com/news/fantasy-football-how-to-get-the-most-out-of-a-pff-subscription-for-fantasy)
- [Fantasy Points Data Suite routes tool](https://data.fantasypoints.com/nfl/tools/player/receiving-routes-run)
- [Fantasy Points Data Suite tools article](https://www.fantasypoints.com/nfl/articles/2024/fantasy-points-data-suite-new-tools)
