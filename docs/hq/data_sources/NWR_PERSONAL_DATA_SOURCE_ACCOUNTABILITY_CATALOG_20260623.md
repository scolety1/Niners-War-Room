# NWR Personal Data Source Accountability Catalog - 2026-06-23

This catalog is for personal review and model accountability. It does not approve any new source, does not wire any source into the app, and does not change ranks, model logic, latest files, pinned snapshots, or frozen boards.

## A. Executive Summary

### What NWR Is Strongest At

NWR is strongest when it uses explicitly frozen or source-truth artifacts with visible guardrails: the Frozen Final Draft Board V1, Sleeper league state/identity after a fresh pull, the LVE PDF page 3 free-agent list for draft eligibility, and NWR's own model outputs when their source contracts and caveats are visible. The repo also has unusually strong governance around leakage: market/rank/projection sources are repeatedly labeled display-only or blocked, and Outcome is forced to say `Not enough information` rather than silently inventing values.

### What NWR Is Weakest At

NWR is weakest where it lacks true historical league state: actual dropped-veteran/free-agent pools over time, complete historical trades, complete current role/injury/news automation, and exact ADP/timing context for this specific rookie/free-agent keeper draft. The model can still produce useful review-only comparisons, but those comparisons must stay humble when they are built from proxy cohorts or mixed source bases. Rows marked `PROXY_DROP`, `PROXY_ONLY`, or `LOW` confidence are sensitivity-only inputs, never direct training truth or source-truth labels.

### Biggest Trust Risks

- Market/ADP/rank/projection data accidentally feeling like NWR value.
- Proxy dropped-veteran history being over-trusted as verified truth.
- PDF-only free agents looking cleaner than they are when unmatched to NWR evidence.
- Outcome coverage gaps being misread as low probability instead of missing evidence.
- Stale player status/team/age/role labels making the app look more certain than it is.
- Vendor data, especially RotoWire/FantasyPros, slipping from research/display context into safe model logic without source-license approval.

### Biggest Missing Data

The P0 gaps are actual historical dropped-veteran league truth, full verified free-agent/draftable pools over time, exact league scoring/roster-construction backtest data, and complete player_id coverage for draftable rows. Those are the gaps most likely to affect on-clock rookie-vs-veteran trust.

### Biggest Available-But-Unused Opportunities

The best future improvements are admitted nflverse participation/first-down/stat coverage, Sleeper historical roster/transaction reconstruction, DynastyProcess player IDs as an identity crosswalk only, CFBD factual college production after identity matching, and admitted factual route/red-zone/usage exports from licensed sources. Market values, ECR, ADP, projections, and trade calculators remain display-only.

## B. Current Source Inventory

| Source | Status | Classification | Accountability Warning |
|---|---|---|---|
| Sleeper API | GREEN for league state; YELLOW for stale metadata risk | source truth for league state and identity; not market/model rank input | Trust roster/availability only after a fresh pull; do not treat Sleeper trends as NWR value. |
| Frozen Final Draft Board V1 | GREEN as frozen baseline, 66 rows | source truth for frozen draft baseline only | If On-Clock Rank disagrees with Final Board Rank, pause for human review. |
| Full NWR Dynasty Board / model_v4 current value | YELLOW because local-only and source freshness must be checked | NWR model output / source truth only for NWR dynasty page after validation | Check whether a player is full-board ranked or draft-board/PDF-only before trusting any rank. |
| Outcome numeric display V1 | YELLOW: 12/66 frozen board support at draft closeout | display-only; never ranking/sort/model input | Never treat missing outcome as zero; treat it as incomplete evidence. |
| LVE Rosters 061326 PDF page 3 | GREEN for draftable free-agent overlay; YELLOW for stale-after-PDF risk | source truth for PDF free-agent draft eligibility; PDF ranks display-only | If a PDF FA is unmatched, draftability is verified but value may be Not enough information. |
| Sleeper ADP display context | YELLOW | display-only market context; should not drive ranks/model logic | Use ADP only to avoid egregious timing mistakes, never as NWR value. |
| nflverse | GREEN for allowed factual stats when imported; YELLOW for missing/current coverage | model input for admitted factual fields; diagnostic for source-risk fields | Ask whether the exact season/source snapshot was loaded before trusting a stats claim. |
| RotoWire local/vendor archive | YELLOW: useful factual fields but source/license review required for safe use | candidate/research-only unless field explicitly admitted; ranks/projections display-only/blocked | If a result depends on RotoWire, treat it as research-only unless a later source-policy review approved it. |
| FantasyPros | YELLOW/RED for model input; display-only where allowed | display-only market/projection; factual advanced fields candidate-only until classified | Any FantasyPros rank/projection-looking field must be presumed display-only or blocked. |
| DynastyProcess | YELLOW: contract defined, not integrated into app/model logic | identity crosswalk candidate; values/ECR display-only market baseline only | DynastyProcess values must never silently become NWR rank or private value. |
| CollegeFootballData / CFBD | YELLOW/UNKNOWN: considered but not production-integrated | candidate factual model input after identity/source gate | Do not trust rookie college-production claims unless a CFBD/local source row is cited. |
| SportsDataIO / API-SPORTS / paid feeds | RED/UNKNOWN for current use; not integrated | blocked/unavailable until licensed and admitted; projections display-only | If a claim says SportsDataIO/API-SPORTS, require license and field admission proof. |
| NFL official / team pages | GREEN for factual sanity checks; not bulk pipeline | diagnostic/sanity check; completed draft facts admitted when cited | Official page facts can correct labels, but should not create a secret ranking adjustment. |
| Pro Football Reference / Sports Reference | YELLOW: useful reference, not a primary automated source | diagnostic/historical factual reference | Check whether stats came from PFR directly or via approved nflverse import. |
| nflfastR / nfl_data_py | YELLOW: considered/used through nflverse family, not always current | admitted factual model input when imported and schema-gated | Ask whether a feature was known before the target season or computed after outcomes. |
| Rookie replay fixtures / historical model v4 reports | YELLOW: valuable but proxy/coverage caveats remain | historical diagnostic / candidate tuning / sensitivity-only where proxy | If a recommendation rests on proxy replay only, label it weaker than verified backtest evidence. |

See `NWR_PERSONAL_DATA_SOURCE_INVENTORY_20260623.csv` for the full current source inventory with paths, cadence, license notes, fields used, available unused fields, pages/lanes, and caveats.

## C. Historical / Backtest Source Inventory

| Artifact | Verified / Proxy | Seasons / Coverage | Training Use | Risk |
|---|---|---|---|---|
| rookie replay fixtures | candidate/proxy | multiple historical classes in reports | sensitivity/model calibration only | future labels must not enter features |
| model v4 current value/full dynasty board | derived NWR output | current snapshot | display/source for NWR rankings after validation | local-only freshness and source evidence required |
| historical cross-asset tuning | candidate/review-only | limited/proxy panels | sensitivity-only unless verified panel exists | proxy dropped veterans cannot dominate formula |
| dropped-veteran proxy cohorts | proxy | 2010-2021 proxy-only | sensitivity/stress/robustness/gap analysis only | not verified league truth; never direct training truth, rank penalty, bad-cut proof, actual-drop evidence, or source-truth label |
| V1 expanded tune outputs | local-only research | historical seasons in run | research-only; not approval | do not commit raw tables; vendor challenger quarantined |
| Outcome sprint 5 internal packages | internal diagnostic | 827-row broader historical set referenced | diagnostic/release-gated | no app probabilities unless release gate approves |
| Frozen Final Draft Board V1 | approved frozen display baseline | 2026 draft day | draft baseline only | not a training set |
| PDF page 3 free-agent pool | verified current draftable overlay | 2026 PDF date | draft eligibility display/source truth | PDF ranks display-only |

Important read: V1/V2 candidate overlays and historical tuning reports are evidence generation, not promotion. Vendor challengers stay quarantined unless source/license approval changes.


## C1. Proxy / Low-Confidence Usage Rule

Rows or artifacts marked `PROXY_DROP`, `PROXY_ONLY`, or `LOW` confidence may be used only for sensitivity testing, stress testing, simulation/backtest robustness checks, and gap analysis. They may not be used as direct training truth, rank penalties, proof a player was a bad cut, evidence that a player was actually dropped, or source-truth labels. `ACTUAL_DROP` and high-confidence `INFERRED_DROP` rows may be analyzed separately, but inferred rows still need caution and should not be over-weighted.

## D. Missing-Data Backlog

| Missing Data | Priority | Current Workaround | Risk If Missing |
|---|---|---|---|
| actual historical dropped-veteran league truth panel | P0 | proxy dropped-veteran cohorts and current PDF overlay | Rookies/veterans can be miscompared |
| complete historical trade data | P1 | manual trade posture only | Trade advice can overstate confidence |
| full verified free-agent/draftable pool over time | P0 | single 2026 PDF page 3 pool | Current available pool may not generalize historically |
| approved 2026 / 2027 / next-5-year Outcome probability artifacts | P1 | horizon bands/candidate notes only | Long-term probability claims remain unsupported |
| current injury/news/role source | P0 | manual official/news sanity checks | Tyreek/Waller/Rice style risks can be understated |
| complete rookie ages/DOB | P1 | roster age context where available; Not enough information otherwise | Missing age weakens candidate rank/confidence |
| complete player_id coverage for frozen board and PDF free agents | P0 | name+position matching fallback | Wrong-player joins or missing evidence |
| current ADP source matching this exact rookie/free-agent keeper draft | P1 | startup ADP display-only weak signal | Current Pick Value can mislead |
| blocked RotoWire/API data source approval | P2 | vendor challenger research-only | Useful route/red-zone metrics cannot become safe candidates |
| missing nflverse/nfl_data_py datasets by season | P1 | partial snapshots/backtests | Backtests can be undercovered by season/position |
| future pick ownership history | P2 | current pick snapshots/manual docs | Pick value and trade context stale/incomplete |
| roster construction/scoring backtest data | P0 | closest internal scoring approximation | Scoring fit may be approximate |
| verified current team/status for needs_data/UNKNOWN rows | P1 | manual flags and Not enough information | Bad team/status label reduces user trust |
| complete snap/route usage coverage | P2 | snap join repaired; route data vendor-limited | Role signal can be missing or biased |
| complete college production and draft capital for rookies | P1 | partial rookie board/manual evidence | Low-confidence rookies can be over/under ranked |
| verified K/DST exclusion policy over all app views | P3 | K/DST hidden by default in current app | K/DST could leak into filters/tables |

See `NWR_PERSONAL_MISSING_DATA_BACKLOG_20260623.csv` for likely source and needed mode for each item.

## E. Available-But-Unused Stats Catalog

| Source | Field / Dataset | Classification | Risk / Guardrail Concern |
|---|---|---|---|
| nflverse | participation/routes/snaps | model input after timing gate | leakage/as-of risk; route coverage uneven |
| nflverse | injuries/depth charts | diagnostic/model confidence only | depth charts are uncertain and can be stale |
| nflverse | pbp first downs | model input after scoring contract | must avoid post-outcome leakage |
| nflverse | combine and draft picks | model input for completed facts | zero placeholders and mock/big-board leakage |
| Sleeper | transactions/rosters over time | model training after archive reconstruction | historical availability may be incomplete |
| Sleeper | player status/team metadata | source truth/diagnostic | metadata staleness |
| Sleeper | traded picks/drafts | source truth for pick state | league/draft id completeness |
| DynastyProcess | db_playerids | identity crosswalk only | GPL/license and name mismatch checks |
| DynastyProcess | values/ecr | display-only market context | must not drive NWR rank/value |
| RotoWire | routes run / TPRR / YPRR | candidate/model input only if licensed/admitted | vendor license and projection/rank contamination |
| RotoWire | red-zone/goal-line usage | candidate/model input only if factual/admitted | small samples and vendor access |
| RotoWire | yards after contact / broken tackles | candidate/model input only if factual/admitted | field definitions and source approval |
| FantasyPros | advanced factual stats | candidate only pending classification | rank/projection leakage risk |
| FantasyPros | ADP/ECR/projections | display-only only | blocked as model input |
| CollegeFootballData | college receiving/rushing/QB stats | model input after identity gate | API key and player matching required |
| CollegeFootballData | team share/context | model input after validation | team/role translations can mislead |
| SportsDataIO | injuries/depth/ids | model input only if licensed/admitted | paid license and projection fields |
| PFF | alignment/routes/charting | candidate only if licensed/admitted | grades/ranks/big boards blocked |
| Official NFL/team pages | transactions/status/injury snippets | diagnostic/source-truth for labels | manual, not bulk; cite URL |
| Pro Football Reference | historical season stats | diagnostic/historical factual | terms and approximate-value misuse |
| Outcome internal package | same-year model diagnostics | diagnostic until release gate | not player-facing unless approved |
| Local model_v4 source risk heatmap | evidence caveat loudness | display/diagnostic | must not become hidden sort |

Available does not mean approved. Each field still needs source timing, leakage, licensing, and identity checks before it can influence NWR value.

## F. Blocked / Optional Sources

- DynastyProcess values/ECR: useful as a market baseline, but display-only. Player IDs may be admitted separately as identity. Values must not become NWR rank/private value.
- FantasyPros ECR/ADP/projections: display-only or blocked. Historical factual advanced stats require separate classification.
- RotoWire projections/ranks/ADP/analyst blurbs: blocked as model input. Factual usage exports remain research-only until license/source review admits them.
- SportsDataIO/API-SPORTS paid feeds: unavailable unless licensed; projections/salaries display-only.
- PFF grades/ranks/big boards: blocked as private value unless a future policy explicitly reclassifies narrow factual charting fields.
- Tankathon mocks/big boards: display-only only; completed draft facts may be verification context.
- External analyst ranks, trade calculators, market values, projections: should not be used for model/rank logic.

## G. Claim Support Map

### Well-Supported Claims

- Frozen board row count and frozen baseline rank are source-truth for the final 66-row board.
- LVE PDF page 3 players are draftable free agents for that PDF snapshot, with K/DST hidden by default.
- Sleeper league state/rosters/picks are admissible league-state facts after a fresh pull.
- Outcome V1 display is partial and must be position-aware/display-only.
- Market/ADP/DynastyProcess/FantasyPros/RotoWire rank-like fields are not safe model inputs.

### Weak / Partial Claims

- Rookie-vs-dropped-veteran cross-asset rank is review-only unless backed by verified historical dropped-veteran league truth.
- PDF-only free-agent value is weak when the player is unmatched to full NWR/Dynasty/player_id evidence.
- 2026/2027/next-5-year horizon outcomes are not approved probabilities unless a future Outcome lane releases them.
- Current injury/status/role claims are only as good as their latest manual/official check.
- Startup ADP/current pick value is weak timing context for this exact rookie/free-agent keeper draft.

## H. Personal Accountability Checklist

A separate checklist is saved at `NWR_PERSONAL_ACCOUNTABILITY_CHECKLIST_20260623.md`. Use it before trusting any NWR output, especially when a player is a PDF-only free agent, has `Not enough information`, or shows a candidate/review-only rank.

## I. External Source Verification Notes

Official/current docs checked during this catalog:

- Sleeper API docs: https://docs.sleeper.com/ - read-only, free, no API token, rate-limit caution.
- nflverse GitHub: https://github.com/nflverse - public NFL data ecosystem and releases.
- CollegeFootballData API: https://api.collegefootballdata.com/ - API key-based college data.
- DynastyProcess data: https://github.com/dynastyprocess/data - open-data repository, weekly GitHub Actions, GPL-3.0 license.
- SportsDataIO NCAA football docs: https://sportsdata.io/developers/api-documentation/ncaa-football - paid/documented sports feeds.

## J. Guardrail Confirmation

This catalog did not edit app code, model code, source artifacts, frozen board, latest files, approved files, pinned snapshot, or `C:\NWR_SHARED_DATA`. It created only personal accountability docs/CSVs under `docs/hq/data_sources/`.
