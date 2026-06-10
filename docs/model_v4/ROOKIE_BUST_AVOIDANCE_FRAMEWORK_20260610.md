# Rookie Bust Avoidance Framework - 2026-06-10

## Purpose

This framework turns the existing historical rookie replay into a scouting and model-review tool. It does not create final draft recommendations. It does not use ADP, public rankings, consensus, market rank, league rank, trade calculators, RotoWire rankings/projections, prior draft history, or legacy private scores as private value inputs.

The goal is to separate:

- real upside
- floor/safety
- bust risk
- evidence quality
- format-adjusted value
- confidence caps

The final NWR score can remain one number, but the detail card should make the hidden tradeoffs visible.

## League Outcome Labels

For this league, labels should reflect a 10-team, 1QB, no-PPR, no-TE-premium format with 2 RB, 3 WR, 1 TE, 2 RB/WR/TE FLEX, and rushing/receiving first downs.

| Label | Meaning |
|---|---|
| Difference-maker | Clear multi-week starter advantage or retained dynasty value edge. Scarce RB/WR production matters more than QB/TE unless format-adjusted evidence is overwhelming. |
| Strong starter | Useful weekly starter or strong flex-level profile over more than a short burst. |
| Useful starter/flex | Player produced enough to matter, but not enough to anchor a dynasty roster. |
| Replacement-level | Replaceable production in a 10-team deep-bench context. |
| Bust | Did not become useful enough relative to rookie draft cost and roster opportunity cost. |
| Injury/uncertain | Outcome contaminated by major availability/context uncertainty. |
| Too early to call | Outcome window is immature. 2024 and 2025 should not drive production formula changes yet. |

Evaluation windows:

- Year 1
- Years 1-2
- Years 1-3
- Best season in first 3 years
- Dynasty value retained after 2-3 years, once a source-safe retained-value label exists

## Repeated Historical Bust / Miss Patterns

Source:

- `local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_rows.csv`
- `local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_summary.csv`
- mature 2021-2023 fantasy-relevant replay rows only

Pattern counts:

| Pattern | Rows | Examples | Model read |
|---|---:|---|---|
| high_ranked_misses | 24 | Kadarius Toney, Rondale Moore, Rashod Bateman, Trey Sermon | Low-evidence/high-rank rows need stronger confidence discipline before weight tuning. |
| low_evidence_overpromotion | 15 | Devonta Smith, Kadarius Toney, Rondale Moore, Javonte Williams | Missing evidence created false certainty. |
| high_ranked_usable_but_not_starter | 14 | Devonta Smith, Javonte Williams, Elijah Moore, Trey Lance | Broad hits are not the same as dynasty edge. |
| low_ranked_strict_starter_hits | 14 | Amon-Ra St. Brown, Justin Fields, Rhamondre Stevenson, Trey McBride | The model can miss real hits when one component is underweighted or missing. |
| low_ranked_difference_makers | 9 | Amon-Ra St. Brown, Brian Robinson Jr., James Cook, Jaxon Smith-Njigba | Upside tail handling needs to survive confidence discipline. |
| first_round_wr_underranks | 6 | Jaylen Waddle, Chris Olave, Jameson Williams, Jordan Addison, Jaxon Smith-Njigba | Round 1 WR floor/target-earning priors likely need review. |
| late_capital_production_false_positives | 5 | Calvin Austin III, Khalil Shakir, Isaiah Spiller, Israel Abanikanda | Production/team-share can fool the model when capital/role path is weak. |
| day_three_rb_hits_worth_preserving | 4 | Rhamondre Stevenson, Kyren Williams, Dameon Pierce, Chase Brown | Late RB upside exists; do not suppress all late-capital RBs blindly. |
| te_overpromotion | 5 | Kyle Pitts, Pat Freiermuth, Hunter Long, Tommy Tremble | No-premium TE caps and exception gates require review. |
| te_underpromotion | 3 | Trey McBride, Sam LaPorta, Tucker Kraft | Elite TE exceptions can be real but need receipts. |
| qb_overpromotion | 1 | Trey Lance | 1QB rookie QB discipline matters. |
| qb_underpromotion | 4 | Justin Fields, C.J. Stroud, Bryce Young | 1QB cap should not erase legitimate QB edge, especially if rushing/age evidence is strong. |

## Pattern Diagnoses

### High-Ranked Misses

What fooled the model:

- low evidence coverage
- production or athletic traits without enough role translation
- draft capital alone creating too much certainty

What would have helped:

- source coverage gates
- stronger missing-evidence confidence caps
- separation of upside and floor

What NWR should do now:

- keep low-evidence top-board rookies in review
- do not promote one-signal players as safe
- detail card should show bust-risk reason, not only upside

### Low-Ranked Hits

What fooled the model:

- underweighted role path
- late-capital RB exceptions
- first-round WR floor/context
- TE development lag

What would have helped:

- stronger role-path evidence
- tail-upside markers
- draft-capital context by position
- target-earning and first-down translation

What NWR should do now:

- preserve upside channels even when confidence caps apply
- avoid a purely conservative model that misses asymmetric hits

### First-Round WR Underranks

Examples:

- Jaylen Waddle
- Chris Olave
- Jameson Williams
- Jordan Addison
- Jaxon Smith-Njigba

Likely issue:

- Round 1 WRs with plausible target-earning profiles may need a stronger floor/safety component.

What NWR should do now:

- review whether established and rookie WR evidence lanes underweight multi-year target earners
- do not use public rankings as targets
- use private production, role, capital, age, and first-down evidence

### Late-Capital RB Hits and False Positives

Examples worth preserving:

- Rhamondre Stevenson
- Kyren Williams
- Dameon Pierce
- Chase Brown

False-positive examples:

- Isaiah Spiller
- Israel Abanikanda
- Evan Hull

Likely issue:

- RB upside is real when role/receiving path and workload translate, but production/team-share alone can overpromote fragile profiles.

What NWR should do now:

- split RB upside from floor
- add a bust-risk lane for fragile role/path profiles
- avoid letting short-window VORP fully represent dynasty horizon

### TE/QB Format Traps

TE examples:

- Kyle Pitts and Pat Freiermuth show TE overpromotion risk.
- Trey McBride, Sam LaPorta, and Tucker Kraft show TE underpromotion risk.

QB examples:

- Trey Lance shows QB overpromotion risk.
- Justin Fields and C.J. Stroud show QB underpromotion risk.

What NWR should do now:

- keep 1QB and no-TE-premium caps, but validate exception gates in replay
- let elite exceptions exist only with private receipts
- avoid a cap that buries legitimate elite QB/TE evidence below replacement rows

## Separate Components NWR Should Expose

Do not hide everything in a single blended score. The model should produce or display:

| Component | Purpose | Example evidence |
|---|---|---|
| Upside score | Ceiling and asymmetry | production ceiling, target earning, explosive role, rushing QB edge, receiving RB path |
| Floor/safety score | Probability of becoming useful | draft capital, role security, multi-year production, age, stable volume |
| Bust-risk score | Fragility and trap detection | low evidence, late capital, athletic-only profile, age, missing role path |
| Evidence/trust score | Source completeness | source receipts, component weight available, identity/status confidence |
| Format-adjusted positional value | League fit | 1QB cap, no-TE-premium cap, 3 WR and 2 FLEX weight |
| Confidence cap | How much certainty the model is allowed to express | missing data, partial first-down evidence, source conflicts |

The final detail card should answer:

- Why does this player have upside?
- Why could this player bust?
- What evidence is missing?
- Is this player safer or more fragile than the rank suggests?

## 2026 Draft Implications

These are profile guidelines only, not final recommendations.

### 2026 1.03 and 1.04

Prioritize profiles with:

- difference-maker upside supported by multiple private evidence lanes
- strong production plus role translation
- credible draft capital or landing context when available
- age/trajectory support
- RB receiving/first-down path or WR target-earning path

Avoid or heavily review:

- one-signal athleticism profiles
- low-evidence top-board profiles
- production-only profiles with weak role/capital support
- QB/TE profiles unless the format-adjusted exception evidence is overwhelming

### 2026 2.04 and 2.08

Prioritize profiles with:

- one or two strong upside signals and a plausible path to role
- first-round WRs or falling WR profiles with private target/role evidence
- RBs with receiving or workload path, not just college box-score volume
- source-limited players only if the missing data is understandable and not structural

Avoid or heavily review:

- late-capital production traps
- small-sample spikes
- landing-spot traps without role evidence
- TE/QB profiles that need premium format assumptions to pay off

### 2026 5.04

This pick remains:

- No Baseline
- Manual late-round watchlist
- No exact equivalence

Useful late-round watchlist profile types:

- role-path outliers
- athletic/production profiles with clear missing-source reason
- late RBs with receiving or first-down path
- source-limited players needing manual scouting

Do not invent a pick baseline for 5.04.

## Immediate Model Recommendations

Do not patch production formulas from this document alone. The next model work should be controlled shadow experiments:

1. Established WR proof/floor lane.
2. RB short-window upside vs dynasty horizon split.
3. TE no-premium exception replay.
4. 1QB cap replay with elite QB floor protection.
5. Missing-evidence policy review: missing evidence should cap confidence, not automatically crush established multi-year stars.
6. Outcome-label rebuild using exact league scoring from raw stats.

## Data Needed Before Final Draft Decisions

- Final legal dropped/released veteran list after Roster Declaration Day.
- Current 2026 rookie draft capital and landing context.
- Better first-down and role-path evidence for rookies.
- Mature outcome windows for recent classes.
- Source-safe dynasty value retention labels.
- Manual scouting notes for low-evidence but high-upside profiles.
