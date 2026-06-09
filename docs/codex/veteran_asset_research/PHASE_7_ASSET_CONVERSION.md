# Research Phase 7 asset conversion framework for LVE

## Core conclusions

The right anchor for LVE is not generic dynasty rank, rookie ADP, or community trade sentiment. It is local surplus value over LVE replacement, adjusted for acquisition cost. That is directionally consistent with value-over-replacement frameworks in fantasy generally and with dynasty trade-chart methodologies that explicitly center replacement-level value and warn that league format assumptions materially change outputs. It is also why public market should sit in a capped liquidity and pricing layer, not in the core private board: entity["company","KeepTradeCut","dynasty calculator"] says its values are crowdsourced, kept in separate 1QB and superflex databases, and based on a vanilla 12-team, .5 PPR, no-TE-premium format that does not adjust for starters, league size, or custom scoring; its own FAQ says calculators are “at best a gut check.” entity["company","FantasyCalc","dynasty trade site"] says its values come from hundreds of thousands to millions of real dynasty trades and that player trade values are averaged with recency weighting. entity["company","FantasyPros","fantasy analytics site"] defines VORP as production above a waiver-level replacement player, while entity["company","Draft Sharks","fantasy football site"] describes dynasty trade values as value over replacement at the position and across positions, with exact league settings as a critical assumption. citeturn4view0turn3search1turn3search3turn18view2turn14view0

For LVE specifically, no-PPR plus 0.4 points per rushing or receiving first down makes “useful NFL touches” more important than raw reception totals. FantasyPros’ PPFD primer found that quarterbacks lose the most value when rushing/receiving first downs are rewarded but passing first downs are not, while running backs gain because they can convert first downs as rushers and receivers; FTN likewise argues that point-per-first-down scoring was designed to offset PPR’s shift toward pass-catchers and notes that first downs are hard to project precisely year to year, so they should be modeled loosely rather than forecast with fake precision. entity["company","Fantasy Points","fantasy analytics site"] has also explicitly treated first downs per route run and QB designed-run/scramble volume as predictive signals, which fits LVE’s desire to reward chain-moving and rushing utility over empty volume. citeturn18view0turn18view1turn9search1turn9search17

The structural suppressions you already proposed are justified. In a 10-team 1QB league, quarterback scarcity is weak unless the QB brings meaningful rushing or elite insulation; in a no-TE-premium format, tight end should usually be priced as an efficiency/role exception rather than a default premium position. Even in standard 12-team VORP tables, a large portion of the QB and TE pool reaches replacement level quickly; by inference, the same scarcity is even flatter in a 10-team 1QB, no-premium league. Meanwhile, your lineup pushes WR and RB demand up: 3 WR starters plus 2 flexes creates a much deeper weekly WR/RB replacement line than most “vanilla” dynasty assumptions. citeturn18view2turn18view3turn19view0turn19view1turn14view0

The veteran-opportunity-cost layer is not optional in LVE. Because the draft happens after roster declaration and each team must release at least one league-rank top-five player, the current-year pick is not just a rookie claim; it is an option on the best remaining rookie, released veteran, or draftable free agent. That means current-year picks in LVE should be valued more like flexible option value than like rookie-only assets, and it also means that generic rookie-class strength should move current LVE pick values less than it would in a rookie-only dynasty draft. That conclusion is league-specific model design, not something the public fantasy market is built to capture.

## Evidence-backed foundations

**Replacement value and league specificity — high evidence.** Cross-asset comparisons should start with replacement level, not with box-score totals or crowd ranks. FantasyPros’ VORP definition and Draft Sharks’ dynasty methodology are both explicit about this, and Draft Sharks is equally explicit that league settings change the entire calculation. citeturn18view2turn14view0

**Public market and liquidity — medium-to-high evidence.** KeepTradeCut says its values are crowdsourced owner averages and its trade calculator is only a gut check; it also states that its liquidity metric is based on the latest 25,000 real trades, and that draft picks are excluded because they are “far and away” the most liquid dynasty assets and would dwarf players if included. FantasyCalc says its values are built from real trades and weighted by recency. For LVE, that supports using public market as a pricing and liquidity layer, not a truth layer. citeturn4view0turn3search1turn3search3

**Scoring-format fit — high evidence.** FantasyPros found that in PPFD-style scoring quarterbacks fall the most while running backs rise on average, especially because RBs can gain first downs two different ways. FTN’s PP1D work reaches the same directional conclusion and further shows that first downs are difficult to project cleanly, which argues for proxy-based scoring inputs rather than a fake exact first-down forecast. citeturn18view0turn18view1

**Age curves and positional volatility — medium-to-high evidence.** Recent aging-curve studies place average peak fantasy seasons around age 25.5 for RBs, 26.9 for WRs, 27.4 raw for TEs but 26.8 once five generational outliers are removed, and 28.5 overall for QBs; the same QB work finds pocket passers peaking later than dual-threats and QB rushing falling sharply after age 29. PFF’s dynasty volatility piece is directionally aligned, describing RBs as the most volatile dynasty assets and WRs as longer-hold “blue-chip” assets. For LVE, that means dynasty-hold value should punish aging RBs more sharply than aging WRs, treat non-elite TEs more like WRs than like immortal outliers, and split rushing QBs from pocket passers. citeturn6search0turn6search1turn6search2turn5search1turn16view0

**Major lower-body injury risk — medium evidence.** Recent and foundational sports-medicine literature on entity["sports_league","NFL","american football league"] skill players shows that Achilles and ACL injuries can materially reduce return-to-play rates, performance, and career duration. A 2021 Achilles study found only 57% RTP among NFL skill-position players, with RBs and WRs particularly vulnerable; ACL literature also shows reduced post-injury per-game and career production for RBs and WRs in multiple cohorts. That supports using major-injury history as a confidence and liquidity penalty, not as a total blackball unless the player’s role already eroded. citeturn12search15turn12search18turn23search0turn23search1turn23search16

**Future-pick discounts and package tax — low evidence, strong practitioner consensus.** There is not strong published evidence for one universal future-pick discount or two-for-one trade tax. What does exist is repeated practitioner acknowledgement that these values are league-specific and should be adjustable: DynastyProcess exposes both a “Future Pick Factor” and “Rookie Pick Optimism” control, Dynasty League Football exposes a draft-pick value adjustment slider and a package adjustment to mitigate “spamming” trades with lesser assets, and KeepTradeCut says its value adjustment also accounts for roster spots and stud concentration. For LVE, exact coefficients here should be treated as model design, stored in fixtures, and calibrated locally over time. entity["company","Dynasty League Football","fantasy football site"] citeturn22view0turn22view1turn4view0

## Unified scale and pick-equivalent interpretation

**Evidence-backed principle.** The scale should measure “if I already rostered this asset, how much LVE value would it hold above local replacement and compared with the other draftable options?” Public market then enters later as liquidity and price discovery, not as the private board itself. citeturn18view2turn14view0turn4view0

**Model-design default.** Use a unified 0-100 scale where 50 is the approximate round-five / last-draftable threshold in the 50-pick post-declaration LVE draft, not the midpoint of all NFL players.

### Common normalized intermediary fields

Before phase 7, every asset should be transformed into the same 0-100 intermediary fields:

| Field | Meaning | Notes |
|---|---|---|
| private_base_score | Your private LVE estimate of the asset before market/liquidity | Core signal |
| year1_score | Expected 2026 usable value in LVE scoring | Current-year utility |
| long_horizon_score | Two- to three-year dynasty hold value | Dynasty shelf life |
| age_curve_score | Position-specific age-window score | Higher is better |
| format_fit_score | LVE fit after no-PPR, first-down, 1QB, no-TE-premium adjustments | Higher is better |
| role_security_score | Stability of role, usage, and lineup survivability | Higher is better |
| replacement_gap_score | Surplus above LVE’s local replacement threshold | Higher is better |
| public_market_score | Capped external market score | Never a core talent input |
| liquidity_score | Ease of moving the asset in trades | Higher is easier |
| confidence_score | Data quality and projection certainty | Higher is safer |
| risk_penalty | Major injury, fragility, role-collapse, suspension, or asset-decay penalty | Applied after weighting |
| current_cost_value | Cost to acquire now in the relevant market | Slot value, trade price, or stash cost |
| accessibility_bonus | Acquisition ease because the asset is on the open board or waivers | LVE-specific |

### Type normalization defaults

These are **model-design defaults** meant to be implemented in fixtures, not hardcoded as eternal truths.

| Asset type | private_base_score | year1_score | long_horizon_score | public_market_score | liquidity_score | accessibility_bonus |
|---|---|---|---|---|---|---|
| Veteran on roster | 0.60 veteran_base_value + 0.25 keeper_score + 0.15 confidence_score | Phase-6 role/projection score; if unavailable use 0.70 veteran_base_value + 0.30 keeper_score | keeper_score | Capped market proxy | Imported or 50 fallback | 0 |
| Released veteran | Same as veteran | Same as veteran | Same as veteran | Same as veteran | Same as veteran | +4 |
| Free agent | 0.55 veteran_base_value + 0.20 keeper_score + 0.25 confidence_score | Role/projection score | keeper_score | 25 default unless imported | 20 default unless imported | +6 post-draft, +2 during draft |
| Rookie player | rookie final_decision_score | rookie_opportunity_score | long_term_dynasty_score | Trade-insulation / capped market proxy | 55 fallback unless imported | 0 |
| Current LVE draft pick | slot_curve_value | slot_curve_value | 0.90 × slot_curve_value | slot_curve_value | 95 | 0 |
| Future LVE pick | current-slot-equivalent × year_discount × slot_uncertainty × class_strength | 0.70 × current-slot-equivalent × year_discount × slot_uncertainty | current-slot-equivalent × year_discount × slot_uncertainty × class_strength | same as private_base_score | 90 next year, 85 two years out | 0 |

### Public market cap

Use public market only after a format mismatch cap:

- public_market_score_capped = minimum of:
  - raw imported market score after LVE format penalty
  - private_base_score + 12

Default LVE format penalties for imported public market:
- QB: minus 12
- TE: minus 8
- RB: minus 0
- WR: minus 0

That cap exists because KeepTradeCut’s baseline is a vanilla 12-team .5 PPR no-TE-premium market and does not adjust for your small 1QB, no-PPR, first-down league; using public market uncapped would systematically overstate QB and many TE values in LVE. citeturn4view0

### Pick-equivalent interpretation

These bands are **model-design defaults** for the 50-pick LVE post-declaration draft board.

| All-asset value | LVE board interpretation | Practical meaning |
|---|---|---|
| 95-100 | Picks 1-3 | Rare cornerstone; top-of-board priority |
| 90-94 | Picks 4-6 | Clear early-round-one target |
| 85-89 | Picks 7-10 | Strong round-one value |
| 80-84 | Picks 11-15 | Late round one / early round two equivalent |
| 74-79 | Picks 16-20 | Strong round-two value |
| 68-73 | Picks 21-27 | Round-three anchor |
| 62-67 | Picks 28-34 | Round-three / early round-four value |
| 56-61 | Picks 35-41 | Round-four value |
| 52-55 | Picks 42-50 | Draftable round-five value |
| Below 52 | Post-draft stash / watch list | Do not spend a top-50 slot unless strategy-specific |

The key LVE twist is that a **current** pick is not a rookie-only coupon. It is an option on the best remaining rookie, released veteran, or free agent. That makes current picks more like flexible option value, while future picks still need time and slot discounts.

## Formula specification

**Evidence-backed principle.** The formulas should be deterministic, league-adjustable, and explicitly configurable because the best-known public tools themselves expose valuation sliders for league context, future-pick discounting, and package adjustment rather than pretending there is one universal equation. citeturn22view0turn22view1turn4view0

**Model-design default.** All coefficients below should live in local CSV or JSON config.

### Core score formulas

| Output | Formula | Notes |
|---|---|---|
| replacement_value | 0.70 × replacement_gap_score + 0.20 × role_security_score + 0.10 × format_fit_score | Clamp to 0-100 |
| win_now_value | 0.45 × year1_score + 0.25 × replacement_value + 0.15 × format_fit_score + 0.15 × confidence_score, then subtract short-term risk penalty | Clamp to 0-100 |
| dynasty_hold_value | 0.35 × private_base_score + 0.25 × long_horizon_score + 0.20 × age_curve_score + 0.10 × role_security_score + 0.10 × confidence_score, then subtract long-term risk penalty | Clamp to 0-100 |
| trade_liquidity_value | 0.45 × public_market_score + 0.35 × liquidity_score + 0.20 × confidence_score | Clamp to 0-100 |
| keeper_adjusted_value | 0.40 × dynasty_hold_value + 0.30 × win_now_value + 0.20 × role_security_score + 0.10 × confidence_score, then subtract cut-cycle penalty | Clamp to 0-100 |
| all_asset_value | 0.32 × keeper_adjusted_value + 0.27 × win_now_value + 0.21 × dynasty_hold_value + 0.12 × trade_liquidity_value + 0.08 × confidence_score, then subtract missing-data and risk penalties | Clamp to 0-100 |
| acquisition_value | 50 + all_asset_value − current_cost_value + accessibility_bonus − roster_spot_cost − package_penalty + consolidation_bonus − liquidity_penalty | Clamp to 0-100 |

### Conversion rules

These rules are deterministic because every conversion reduces to the same two comparisons: intrinsic value and current acquisition price.

| Conversion | Deterministic rule |
|---|---|
| Veteran to rookie pick | Convert veteran to all_asset_value, then find the nearest current LVE slot band whose slot_curve_value matches that score. Example: an 84-value veteran is roughly a pick-11-to-15 asset in LVE. |
| Rookie to veteran | Compare rookie all_asset_value to veteran all_asset_value. If within 4 points, break ties toward the higher confidence score or the more scarce RB/WR profile. |
| Pick to player | Compare player acquisition_value at the current slot. If player acquisition_value is above 55, the player is a positive-value selection at that pick. If below 45, trade down or pass. |
| Future pick to current pick | current-slot-equivalent × year_discount × slot_uncertainty × class_strength. Use all_asset_value after discounting, then compare with current slot_curve_value. |
| Released veteran to rookie slot | Treat the released veteran exactly like any veteran, but add accessibility_bonus because there is no incumbent manager premium. Compare acquisition_value at the current pick. |
| Free agent to roster stash | Use veteran/free-agent all_asset_value, then compare against stash threshold and roster spot cost. If post-draft acquisition_value is above 55 or all_asset_value is at least 48 with a real upside path, the stash is justified. |

### Future-pick discount defaults

These are **model-design**, not sourced coefficients.

| Year offset | Year discount |
|---|---|
| Current year | 1.00 |
| One year out | 0.90 |
| Two years out | 0.80 |
| Three years out | 0.72 |

### Slot-uncertainty defaults

| Pick expectation | Slot uncertainty factor |
|---|---|
| Known current slot | 1.00 |
| Projected early | 0.96 |
| Projected mid | 0.92 |
| Projected late | 0.87 |
| Unknown external pick | 0.90 |

### Class-strength defaults

Because LVE current picks can become veterans as well as rookies, class-strength should move values less than in a rookie-only model.

| Class view | Multiplier |
|---|---|
| Weak | 0.96 |
| Neutral | 1.00 |
| Strong | 1.04 |

## Replacement thresholds and trade package math

**Evidence-backed principle.** Replacement thresholds should reflect lineup demand, not generic rank lists. VORP-style frameworks compare players to a waiver-level replacement, and Draft Sharks’ dynasty methodology likewise emphasizes replacement level and exact roster settings. In LVE, the base lineup creates 10 QB starts, 20 RB starts, 30 WR starts, 10 TE starts, and 20 flex starts across the league. Because this is no-PPR with first-down scoring, flex should tilt more toward RB than it would in full PPR, but 3 mandatory WR starters still makes WR demand very deep. citeturn18view2turn14view0turn18view0turn18view1

**Model-design default.** Start with a flex-allocation assumption of 60% WR, 35% RB, and 5% TE until you have local lineup history to replace it.

### LVE replacement thresholds

| Position | Effective weekly starter demand | Weekly replacement threshold | Deep-roster stash threshold | Elite anchor |
|---|---:|---:|---:|---:|
| QB | 10 | QB13 | QB18 | QB6 |
| RB | 27 | RB32 | RB46 | RB12 |
| WR | 42 | WR46 | WR60 | WR15 |
| TE | 11 | TE14 | TE18 | TE5 |

### Replacement-gap scoring

Use projected LVE positional rank, not generic site rank.

- If projected rank is at or above the elite anchor, set replacement_gap_score between 85 and 100.
- If projected rank equals the weekly replacement threshold, set replacement_gap_score to 50.
- If projected rank equals stash threshold, set replacement_gap_score to 20.
- If projected rank is worse than stash threshold by more than six slots, set replacement_gap_score to 0.
- Interpolate linearly between thresholds.

### Package math

**Evidence-backed principle.** Public dynasty tools explicitly correct for package spam and roster spots. KeepTradeCut says its value adjustment accounts for roster spots, stud factor, and the number of lesser players; Draft Sharks says 2-for-1 and 3-for-1 deals require a “trade tax” because the single stud fills one lineup slot while the other side must either use two slots or cycle waiver depth; Dynasty League Football exposes a package adjustment for the same reason. citeturn4view0turn14view0turn22view1

**Model-design defaults.**

### Two-for-one and three-for-one package penalty

Package penalty = stud tax + net roster-spot cost.

Stud tax rate by highest-value incoming asset:
- under 70: 0%
- 70 to 79: 15%
- 80 to 89: 25%
- 90 and above: 35%

Stud tax = highest incoming all_asset_value × tax rate.

Net roster-spot cost:
- each extra roster slot you must open beyond the trade balance: 3 points
- example: sending 2 for 1 means 1 extra slot must be created on the other side, so apply 3 points to the multi-asset package before comparing values

### Consolidation premium

Use only when the incoming asset improves a true startable slot.

- plus 2 for upgrading into a clear WR/RB weekly starter
- plus 4 for upgrading into a top-15 overall LVE board asset
- plus 0 for QB or TE unless the player is already above the elite anchor

### Liquidity penalty

Apply in acquisition_value, not in private all_asset_value.

- liquidity 60 or higher: 0
- liquidity 40 to 59: minus 3
- liquidity 25 to 39: minus 6
- liquidity below 25: minus 10

### Overpay thresholds

These are the largest negative fair-value gaps you should usually tolerate.

- Young WR/RB with all_asset_value 85 or higher: up to 8
- Released veteran WR/RB with clear week-one starting value: up to 5
- Elite QB or elite TE exception: up to 3
- Non-elite QB or TE: 0 to 2
- Aging RB rental: 0 to 3
- Low-confidence rookie: 0

## Draft-room rules and forced-release adjustments

The most important LVE rule is simple: **pick the best acquisition_value on the board, not the best rookie score.** Because the annual draft is post-declaration and includes rookies, released veterans, and free agents, your current pick is a temporary option on the whole market, not just on the rookie class.

### Draft-room decision rules

**When a rookie beats a veteran**
- The rookie’s acquisition_value is at least 4 points higher.
- Or the rookie’s all_asset_value is at least 8 points higher and the confidence gap is no worse than 10.
- Or the rookie is a WR/RB with upside and long-horizon edge, while the veteran is in a position-specific red age zone.

**When a veteran beats a rookie**
- The veteran’s acquisition_value is at least 4 points higher.
- Or the veteran’s win_now_value beats the rookie’s by at least 10 and the veteran still clears a keeper_adjusted_value of 65.
- In rounds 2 through 5, prefer the veteran at parity unless the rookie has both an upside flag and a better long_horizon_score.

**When a pick beats a player**
- A trade-down preserves access to the same tier while gaining at least 5 slot-value points.
- Or the board is flat and the current pick retains more option value than any single available non-elite player.
- In ties, prefer the pick because picks are the most liquid dynasty assets in the public market. citeturn4view0

**When to trade down**
- Three or more same-tier assets remain within 5 all_asset_value points.
- The best trade-down offer adds at least 5 value points after package and roster penalties.
- Do this more aggressively if the remaining tier is QB/TE heavy.

**When to trade up**
- A clear tier cliff of at least 8 points exists.
- The target is a WR or RB, or a truly elite QB/TE exception.
- Do not trade up for non-elite QBs in 1QB or non-elite TEs in no-premium.

**When to pass on low-confidence assets**
- confidence_score below 55 and no exceptional upside flag
- confidence_score below 50 for QB/TE
- severe risk penalty without a matching discount in current_cost_value

### Forced-release adjustments

These are pure LVE model design.

- Lower the rookie-only premium across the entire current draft because the board includes released veterans and free agents.
- Flatten the early slot curve modestly, especially from picks 8-25, because the supply of usable veterans rises after declaration.
- Suppress QB and TE even further when startable released options exist, because replacement is already easy in 1QB and no-premium.
- Give released veterans an accessibility_bonus of +4 by default because they do not require persuading another manager to sell.
- Never use official league rank as a direct talent or value input. Use it only:
  - before declarations, as a release-likelihood tag
  - after declarations, as a provenance tag showing why the player is available  
  Once the player is on the board, the “top-five” label should have zero effect on private value.

## CSV schema recommendations and test fixtures

### CSV files

These are additive, phase-7-specific files that sit on top of the prior rookie and veteran model outputs.

| File | Purpose | Required columns |
|---|---|---|
| asset_master.csv | One row per asset in the draftable universe | asset_id, asset_type, player_name, position, nfl_team, season, is_released, is_free_agent, is_pick, pick_year, pick_slot, age, status, provenance_note |
| asset_market_proxies.csv | Frozen external market inputs, manually entered or imported | asset_id, source_name, source_format, source_date, market_score_raw, liquidity_raw, manual_override, provenance_note |
| lve_pick_curve.csv | Local slot-value curve and future-pick discounts | season, board_slot, slot_curve_value, year_offset, year_discount, slot_bucket, slot_uncertainty_factor, class_strength_multiplier |
| lve_replacement_thresholds.csv | Position thresholds and flex assumptions | season, position, weekly_replacement_rank, stash_threshold_rank, elite_anchor_rank, flex_share_assumption, notes |
| asset_conversion_inputs.csv | Intermediary normalized values | asset_id, private_base_score, year1_score, long_horizon_score, age_curve_score, format_fit_score, role_security_score, replacement_gap_score, public_market_score, liquidity_score, confidence_score, risk_penalty, current_cost_value, accessibility_bonus |
| asset_conversion_outputs.csv | Final asset-conversion layer | asset_id, replacement_value, win_now_value, dynasty_hold_value, trade_liquidity_value, keeper_adjusted_value, all_asset_value, acquisition_value, pick_equivalent_low, pick_equivalent_high, decision_bucket, notes |
| asset_provenance_notes.csv | Audit-only notes, handwritten history, manual corrections | asset_id, field_name, note_type, source_description, entered_by, entered_date, confidence_impact |

### Data-handling rule

Public market inputs must be frozen and local. KeepTradeCut’s FAQ expressly forbids scraping or reproducing its full values in other resources, and your project rules already prohibit scraping and live APIs. So market inputs should be manually entered, CSV-imported from permitted sources, or stored as small provenance-backed snapshots rather than fetched at runtime. citeturn4view0

### Test fixture recommendations

These fixtures should be deterministic and anchored to fixed local CSVs.

| Fixture | Setup | Expected result |
|---|---|---|
| Released veteran WR beats similar rookie | Released WR with all_asset_value 88, confidence 84 vs rookie WR 84, confidence 67 at slot 1.08 | Veteran chosen; acquisition_value higher |
| Elite rookie RB still wins | Rookie RB 93 vs aging released RB 84 at 1.01 | Rookie chosen |
| Pocket QB suppression | QB with all_asset_value 79 but no rushing and moderate liquidity vs WR/RB in same band | QB pushed down in board order |
| Elite rushing QB exception | Rushing QB with 90+, strong confidence, elite age window | Can enter late round-one / early round-two band |
| Non-elite TE suppression | TE 74 with ordinary market support | Falls behind same-tier WR/RB |
| Elite TE exception | TE 83 with elite year1 and long-horizon scores | Can beat round-two board tier, but still not auto-premium |
| Future early first vs aging RB rental | Future early first 72 vs veteran RB 71 with poor age curve | Pick preferred unless explicitly win-now build |
| Current pick beats player in flat tier | Slot 2.04 with three assets 71-73 and trade-down adds 6 points | Trade down preferred |
| Released veteran beats rookie slot | Released RB2 or WR3 at slot 3.02 with acquisition_value 58 vs rookie dart at 49 | Veteran chosen |
| Post-draft free-agent stash | Free-agent RB handcuff all_asset_value 49, accessibility +6, good upside | Stash approved |
| Free-agent QB not worth stash | Pocket QB all_asset_value 44 in 1QB | Not a priority stash |
| Package-spam rejection | Two 56-value assets for one 86-value WR | Reject after package penalty and roster-spot cost |

## Rejected shortcuts and dangerous assumptions

Do **not** use crowd or trade-calculator values as your private board. KeepTradeCut itself says its trade calculator is a gut check, its values are based on a vanilla 12-team .5 PPR format, and it does not adjust for starters, league size, or custom scoring. FantasyCalc’s value sources are real trades, which is useful for price discovery, but real trades are still public-market behavior, not LVE truth. Public market belongs in liquidity and cost overlays only. citeturn4view0turn3search1turn3search3

Do **not** treat current LVE picks like generic rookie-only picks. In your league, current picks buy access to the entire post-declaration market, so the pick curve should be based on expected best-available open-board value, not on rookie ADP alone.

Do **not** import exact future-pick discounts from another site as if they were evidence. The best-known dynasty tools openly expose future-pick and rookie-pick sliders because those settings are contextual and judgment-driven. citeturn22view0turn22view1

Do **not** let league-rank top-five status enter core value. It is an availability flag for the forced-release rule, not a talent metric.

Do **not** skip roster-spot and package penalties. Every major dynasty calculator that tries to handle 2-for-1 trades adjusts for stud concentration, package spam, or roster spots for a reason. citeturn4view0turn14view0turn22view1

Do **not** overvalue pure reception archetypes in LVE. No-PPR plus first-down scoring makes empty catches less useful than chain-moving targets and dual-use RB touches. citeturn18view0turn18view1

Do **not** overpay for QB or TE absent an elite exception. In a 10-team 1QB league with no TE premium, replacement cliffs are too soft to pay generic dynasty prices for middle-tier assets at those positions. citeturn18view2turn19view1turn4view0

Do **not** treat major lower-body injury history as neutral. The literature is too clear that Achilles and ACL injuries can reduce return-to-play odds, performance, or career length for NFL skill players. They belong as confidence and liquidity penalties at minimum. citeturn12search15turn23search0turn23search1

The practical bottom line for Niners Dynasty War Room is this: build phase 7 around one deterministic question at every decision point — **what asset gives the highest acquisition_value at this specific LVE price right now?** Everything else, including rookie score, veteran projection, future picks, and public market, should feed that one comparison.