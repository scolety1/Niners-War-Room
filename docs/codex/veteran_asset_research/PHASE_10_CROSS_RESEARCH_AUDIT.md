# Final Cross-Research Audit and Contradiction Check for LVE

## Audit scope and executive verdict

This audit evaluates the architecture implied by Phases 6–9 rather than line-by-line prose from those phases, because the full text of those reports is not reproduced in this thread. I am therefore auditing the **proposed framework**, its cited evidence base, and the likely implementation choices that would follow from it.

The overall direction is **sound**. A local-first, deterministic, table-first model that uses league-specific replacement value, separates private value from trade liquidity, and compares rookies against released veterans/free agents is the right architecture for LVE. The largest problems are not the broad ideas; they are the **precision claims**, especially where the framework risks pretending that heuristic coefficients are evidence-backed, or where it double-counts role, opportunity, and first-down value. The strongest evidence in this space supports three things: fantasy value must be evaluated relative to **replacement options in the specific league context**; **projections are generally more useful than rankings** when you need scoring-specific outputs; and **multiple independent sources combined transparently** are usually more reliable than picking one “best” source. citeturn6view1turn6view6turn6view11turn22view1

The biggest corrections before coding are these. First, keep **private roster value** and **public market/liquidity value** as separate ledgers; do not blend market rank directly into core veteran scoring. Second, make **replacement thresholds state-dependent**: LVE has a normal dynasty state and a post-declaration/offline-draft state, and those are not the same market. Third, move **official injury reports and scoring-adjusted projections** above market ranks and unofficial depth charts in the source hierarchy. Fourth, treat **most exact coefficients from Phases 6–9 as model-design**, not evidence-backed truth. Fifth, keep **QB and TE suppression**, but implement them as **soft, replacement-based structural discounts with elite-outlier escape hatches**, not rigid ceilings. Those conclusions line up with how replacement value depends on roster settings, how public consensus systems are built on half-PPR assumptions, how projections adapt to custom scoring more naturally than ranks do, and how official injury reporting is materially more structured than publicly posted depth charts, which teams often label “unofficial.” citeturn6view1turn6view5turn21view0turn21view1turn6view6turn18view0turn6view8turn19view0

| Question | Verdict | Audit note |
|---|---|---|
| Is the directionally correct architecture in place? | **Yes** | League-specific replacement value, deterministic scoring, and a unified rookie/veteran/released-player decision layer are all conceptually right for LVE. citeturn6view1 |
| Is the current approach overcomplicated? | **Yes, at the coefficient layer** | The framework has too many places where weakly sourced or unsourced exact numbers can masquerade as truth. The evidence is stronger on inclusion/direction than on exact weights. citeturn20view0turn6view11 |
| Is the CSV/schema approach appropriate? | **Yes, with limits** | CSVs are good for local-first provenance and deterministic tests, but generated outputs should not become hand-edited source-of-truth data. |
| Is the veteran-opportunity-cost layer necessary? | **Yes** | In LVE, draft-day value is explicitly relative to the available veteran/free-agent pool, not just rookie peers. Replacement value logic requires that comparison. citeturn6view1 |
| Is QB/TE suppression justified? | **Yes, but softly** | 1QB and no-TE-premium/no-SF clearly reduce scarcity. The mistake would be turning that structural truth into inflexible bans that ignore elite outliers or temporary declaration-window value pockets. PPFD-style scoring also tends to hit QBs relative to non-QBs while helping players who generate rushing/receiving first downs. citeturn17view0turn17view2 |

## Contradiction table

| Topic | Conflicting claims | Which phase or source made each claim | Recommended resolution | Confidence level |
|---|---|---|---|---|
| Replacement baseline | Veteran scoring implicitly values players in a deep-bench dynasty environment, while the asset-conversion and draft-room layers treat rookies, released veterans, and free agents as direct same-day substitutes. | Phase 6 veteran framework vs. Phase 7 unified asset conversion vs. Phase 8 forced-release draft-room logic. | Create **two replacement baselines**: `steady_state_replacement_value` for keeper/trade decisions and `declaration_window_replacement_value` for the offline draft after releases. Use the second one in rookie-vs-veteran decisions. Replacement value is league-setting dependent by definition. citeturn6view1 | **High** |
| Public market vs. private value | The veteran model says public market should be capped and separated from private value, but the asset-conversion framework also wants trade liquidity and pick-equivalent math. | Phase 6 veteran value brief vs. Phase 7 trade/liquidity brief. | Keep **two ledgers**: `private_roster_value` and `trade_liquidity_value`. Never average public market ranks directly into `veteran_base_value` or `all_asset_value`. Use them only in a separate liquidity or trade layer. Public consensus systems also operate in half-PPR ecosystems, not LVE scoring. citeturn6view5turn21view0turn21view1turn6view6 | **High** |
| Rankings vs. projections | The source/confidence layer allows market ranks and consensus rank use, but the scoring model requires league-specific outputs for no-PPR plus first-down scoring. | Phase 7 asset conversion vs. Phase 9 source hierarchy. | Use **projections as the core numeric source** and **rankings as secondary market/liquidity context only**. One crowd study found projections more accurate than rankings overall and especially for QB/WR/TE, and projections are directly adaptable to custom scoring formats. citeturn6view6turn21view0turn21view1 | **High** |
| First-down scoring transfer | The model likely elevates first-down traits because LVE awards 0.4 points for rushing/receiving first downs, but most public PPFD analyses use full PPFD or 0.5 systems and often discuss seasonal rank shifts, not predictive weights. | Phase 6 veteran scoring brief vs. Phase 7 asset conversion brief vs. public PPFD articles. | Transfer only the **direction**, not the magnitude. LVE should reward chain-moving role, but the first-down bonus should be smaller than in full-PPFD studies and should usually live as a **league-fit overlay** or residual adjustment, not a large separate core feature. Full-PPFD analyses show that QBs lose value and RBs gain relative value, but that is not a license to import their exact deltas into LVE. citeturn17view0turn17view1turn17view2 | **High** |
| First-down metrics vs. role metrics | The model wants first-down profile, role/projection, touches, target share, and chain-moving indicators all together. | Phase 6 veteran feature set vs. Phase 7 asset conversion. | Avoid **double-counting**. If the base projection already converts usage into LVE scoring, do not separately add large weights for first downs, target share, snap share, and role certainty unless you are explicitly using them as projection-quality, confidence, or residual signals. First-down efficiency is also heavily role/usage dependent. citeturn17view1turn17view0 | **High** |
| Depth-chart certainty | Role/projection rules will naturally want depth-chart inputs, but the source policy wants reliability and explainability. | Phase 6 role/projection rules vs. Phase 9 source hierarchy. | Demote depth-chart ordering to **secondary or display-only**. Official injury reporting has mandated specificity and timeliness; team depth charts are often explicitly labeled **unofficial** on club sites. Opportunity should come from projection consensus, roster moves, and practice/injury information first. citeturn18view0turn6view7turn6view8turn19view0 | **High** |
| Contract security | The veteran model may want contracts to signal keeper safety or short-term role security, but contract sites themselves reflect nuance and assumptions that are easy to oversimplify. | Phase 6 contracts input vs. Phase 9 source policy. | Contracts should be a **secondary job-security modifier**, not core scoring. “Guaranteed” money is not binary, and public cap sites can differ because of timing assumptions, per-game roster bonuses, and other contract mechanics. citeturn6view10turn25view0 | **Medium-High** |
| Age curves vs. hard cliffs | Age-curve rules by position are required, but a deterministic model can drift into single-age cliff logic. | Phase 6 age-curve rules vs. Phase 7 hold/win-now formulas. | Use **age bands and risk flags**, not one single exact age cutoff. RB decline is earlier than WR; TE and QB age differently; and aging studies explicitly warn about survivorship/selection bias. Exact cliff points should be treated as heuristics. citeturn7view5turn7view4turn6view3turn9view2turn20view0 | **High** |
| QB suppression | The framework wants hard QB suppression in 1QB, but it also needs to account for elite rushing QBs and declaration-window pocket value if a strong veteran is forced into the pool. | Phase 6 veteran QB framework vs. Phase 7 unified asset conversion. | Keep structural suppression, but implement it as a **soft discount around replacement**, not a hard ceiling. PPFD-like formats hurt QBs overall, but rushing QBs lose much less value than pocket QBs; separately, rushing output tends to decline with age/experience, so long-term dynasty value should not assume fixed rushing levels forever. citeturn17view0turn9view0turn24search1 | **High** |
| TE suppression | The framework wants strong TE suppression in no-premium, but elite TEs age differently and remain useful for longer than RBs. | Phase 6 veteran TE framework vs. Phase 7 all-asset conversion. | Keep TE structurally below RB/WR unless elite, but do not make the TE penalty unconditional. The evidence supports slower TE development and later useful age windows, but also warns that some TE samples are small. That means coarse priors, not precise cliffs. citeturn6view3turn7view2turn17view0 | **Medium-High** |
| Injury handling | The source policy can tempt the model to overreact to every injury listing, while the veteran model wants injury/durability rules. | Phase 6 injury rules vs. Phase 9 source/confidence policy. | Do not score “injured” as a blunt variable. Use **injury type, time-loss, recovery status, and position sensitivity**. Official injury reports are structured but not sufficient by themselves. Orthopedic literature is stronger: ankle injuries and ACL reconstruction materially reduce RB/WR/TE production, while QBs are generally less affected in the same way. citeturn18view0turn12search4turn13search0 | **High** |
| Future-pick discounting | Asset conversion likely wants fixed future-pick discounts, but forced-release dynamics create yearly veteran supply shocks that change current-pick opportunity. | Phase 7 future-pick conversion vs. Phase 8 forced-release strategy. | Do **not** use one global future-pick discount. Discount by a combination of time, uncertainty, and expected declaration-window replacement supply. There is strong support for replacement-level thinking, but not for one universal dynasty pick discount. citeturn6view1 | **Medium** |
| Manual overrides vs. determinism | Phase 9 requires manual overrides and handwritten-history handling, but the app’s design requires deterministic and explainable outputs. | Phase 9 override policy vs. all scoring phases. | Allow overrides to **inputs, provenance, source selection, and scenario assumptions** only. Do not allow silent direct edits to output scores. Forecast-combination research favors transparent combination rules over picking a single source or silently hand-editing results. citeturn6view11turn22view1 | **High** |
| Forced-release owner modeling | Phase 8 wants pressure scores, urgency scores, and opponent target scores, but owner behavior, league-rank uncertainty, and reacquisition behavior are only weakly observable. | Phase 8 forced-release strategy vs. Phase 9 confidence policy. | Treat owner-behavior coefficients as **scenario outputs with wide confidence bands**, not as hard scoring inputs. Until there is enough LVE history, these should be **display-heavy and weight-light**. | **High** |

## Evidence-strength downgrade table

Because the full wording and labels from Phases 6–9 are not reproduced here, “original confidence” below refers to how the current framework appears to treat each claim.

| Claim | Original confidence | Corrected confidence | Reason |
|---|---|---|---|
| First-down scoring should be a **large direct core weight** in veteran scoring. | High | **Medium** | The direction is real, but much of the public analysis is PPFD strategy content rather than predictive validation. First-down efficiency is also heavily role-driven, which raises double-counting risk. citeturn17view0turn17view1turn17view2 |
| Public consensus rankings are good enough to act as a core valuation input. | Medium-High | **Low** | Consensus ranks are useful market context, but FantasyPros accuracy and ECR operate in half-PPR environments, while league-specific projections are adaptable to LVE scoring and often more accurate than ranks for QB/WR/TE. citeturn21view0turn21view1turn6view6turn6view5 |
| Depth-chart ordering is reliable enough to score opportunity directly. | Medium | **Low** | Official injury reports are regulated and specific; official team depth charts are often explicitly marked “unofficial.” citeturn18view0turn6view8turn19view0 |
| Contract guarantees strongly equal keeper safety. | Medium | **Low** | “Guaranteed” money can be practical, vesting, or injury-based, and public cap sites can differ based on assumptions. Treat contracts as context, not core truth. citeturn6view10turn25view0 |
| Veteran age can be handled with exact cliff ages. | Medium-High | **Medium** | The broad positional aging order is well supported, but exact cliff ages are far less stable because of survivorship bias, era effects, and small samples for some positions. citeturn20view0turn7view5turn6view3 |
| Mobile QBs are inherently more injury-prone than pocket QBs. | Medium | **Low / likely false** | Available fantasy-oriented injury work says there is no clear evidence that mobile QBs are injured more often or more severely simply because they run. The larger issue is that rushing share tends to fall as QBs age. citeturn10search1turn24search1turn9view0 |
| The QB suppression rule should be hard and universal in 1QB. | Medium | **Medium-Low** | Structural suppression is correct, but full rigidity is not. Rushing and declaration-window replacement context can still create meaningful QB value pockets. citeturn17view0turn9view0 |
| The TE suppression rule should be hard and universal in no-premium. | Medium | **Medium-Low** | The no-premium setup lowers TE value, but TE aging and development windows differ from RB/WR, and elite route-earning TEs can still matter. Some TE sample bases are explicitly small. citeturn6view3turn7view2 |
| Every injury designation should materially move veteran value. | Medium | **Low** | Not all injuries are equal; official designations are structured but not severity scores. Stronger evidence supports position- and injury-type-specific penalties, especially for lower-body injuries to RB/WR/TE. citeturn18view0turn12search4turn13search0 |
| A fixed future-pick discount can be implemented before calibration. | Medium | **Speculative** | No strong public evidence supports one universal dynasty future-pick discount, especially in a league with forced releases that alter short-run replacement supply. citeturn6view1 |
| Two-for-one penalties, consolidation premiums, and liquidity penalties can be set with confidence before testing. | Medium | **Speculative** | These are useful model-design levers, but there is no strong public evidence producing LVE-specific constants for them. |
| Forced-release urgency and opponent-release scores can be sharply quantified before you build LVE history. | Medium | **Speculative** | Owner behavior, declaration timing, and reacquisition choices are league-behavior problems, not strongly sourced football-performance problems. |

## Coefficient audit

The single most important audit conclusion is this: **almost none of the exact numeric weights that Phases 6–9 would likely require are directly evidence-backed**. The evidence supports **feature inclusion, direction, and broad ordinal importance**. Exact percentages, gates, penalties, and package coefficients are overwhelmingly **model-design heuristics** and should be labeled that way.

| Coefficient family | What the evidence actually supports | Audit result | Before-money-decision status |
|---|---|---|---|
| Veteran base-value dependence on replacement level | Strong support that player value depends on league size, lineup, and replacement level rather than raw points alone. citeturn6view1 | **Accept as evidence-backed direction** | Use; exact threshold values still need local calibration. |
| Projection-over-ranking preference | Moderate support that projections outperform rankings overall and are better for custom scoring; rankings still matter for market/liquidity. citeturn6view6turn21view0turn21view1 | **Accept as evidence-backed direction** | Use; keep rankings secondary. |
| Combining multiple sources in confidence logic | Strong generic forecasting support that combining multiple forecasts usually improves robustness. citeturn6view11turn22view1 | **Accept as evidence-backed direction** | Use; exact completeness/freshness/agreement weights remain heuristic. |
| Official injury report priority | Strong support that official injury reports are structured, specific, and time-bound. citeturn18view0turn6view7 | **Accept as evidence-backed** | Use. |
| Depth-chart downgrade | Good support that club depth charts are often labeled unofficial. citeturn6view8turn19view0 | **Accept as evidence-backed direction** | Use as secondary/display-only. |
| Position-specific age curves | Good support for the broad order: RB earlier decline, WR later, TE later still, QB latest, with survivorship caveats. citeturn7view5turn7view4turn6view3turn9view2turn20view0 | **Accept as evidence-backed direction** | Use broad bands, not exact cliff coefficients. |
| Injury penalties by type and position | Good support that ankle and ACL injuries depress RB/WR/TE performance more than QB; weak support for single-number universal penalties. citeturn12search4turn13search0 | **Partially evidence-backed** | Use injury-type flags; test penalty sizes. |
| QB structural suppression in 1QB | Supported by replacement logic and scoring-format direction, but not by one exact numeric gate or universal cap. citeturn6view1turn17view0 | **Heuristic with strong rationale** | Test; do not hard-code as absolute ceiling. |
| TE structural suppression in no-premium | Supported by lineup economics and no-premium logic, but not by one exact coefficient. citeturn6view1turn17view0 | **Heuristic with strong rationale** | Test; allow elite escape hatch. |
| First-down feature weights | Supported directionally, especially as a scoring overlay, but not by strong evidence for one specific direct weight in veteran scoring. citeturn17view0turn17view1turn17view2 | **Mostly heuristic** | Keep small unless used as residual after base projection. |
| Public-market cap size | No strong public evidence for one correct cap percentage. | **Model-design heuristic** | Test locally before relying on it. |
| Future-pick discount rate | No strong public evidence for a universal dynasty discount, especially with forced-release supply shocks. | **Model-design heuristic** | Must be calibrated; do not trust default constants. |
| Two-for-one penalty | No robust public evidence for one roster-cost coefficient. | **Model-design heuristic** | Test locally with LVE roster pressure. |
| Consolidation premium | Rational in theory, but coefficient size is heuristic. | **Model-design heuristic** | Test. |
| Liquidity penalty for niche assets | Rational in theory, but coefficient size is heuristic. | **Model-design heuristic** | Test. |
| Forced-release pressure weights | No public evidence supports exact score construction for owner behavior in LVE. | **Model-design heuristic** | Display-focused until LVE history exists. |
| Manual-override penalty/boost | Forecast literature supports transparent source combination, not silent overrides; the exact override penalty is heuristic. citeturn6view11turn22view1 | **Partially evidence-backed** | Use small penalties; log everything. |

## Implementation change list

| Item | Disposition | Why | Exact change |
|---|---|---|---|
| Replacement value as a core concept | **Accept as-is** | This is the strongest methodological backbone in the whole framework. citeturn6view1 | Keep it central. |
| Single replacement threshold for all contexts | **Stop and review** | LVE has normal-state valuation and declaration-window valuation. | Split into `steady_state` and `declaration_window` replacement baselines. |
| Projections as main numeric input | **Accept as-is** | Better fit for custom scoring and generally more accurate than rankings, especially at QB/WR/TE. citeturn6view6turn21view0turn21view1 | Make the primary core input class `projection_based`. |
| Public ranks as core player value | **Reject / display-only** | Half-PPR rank ecosystems are not LVE scoring and are not the best core signal. citeturn21view0turn21view1turn6view6 | Move to `trade_liquidity_value` or market display only. |
| First-down profile as core weight | **Accept with lower confidence** | Directionally useful in LVE, but direct coefficient should be modest and residual-based. citeturn17view0turn17view1turn17view2 | Use only if not already embedded in projection or role estimates. |
| Depth-chart slot as scored feature | **Needs better source** | Team depth charts are often unofficial. citeturn6view8turn19view0 | Downgrade to secondary input or display-only warning. |
| Official injury report priority | **Accept as-is** | Strongest official weekly availability signal. citeturn18view0turn6view7 | Put above market notes and social reporting. |
| Contract-based security score | **Accept with lower confidence** | Contracts matter, but guarantees are nuanced and public sites differ. citeturn6view10turn25view0 | Use only as a small confidence/risk modifier. |
| Hard age cliffs | **Reject / rework** | Broad age bands are supported; exact cliffs are not. citeturn20view0turn7view5turn6view3 | Replace with banded risk flags by position. |
| Hard QB and TE ceilings | **Accept with lower confidence** | Structural suppression is right, but hard ceilings are too rigid. citeturn17view0turn9view0 | Convert to soft penalties with elite-exception gates. |
| Fixed future-pick discount | **Stop and review** | No strong evidence for one number; declaration-window supply matters. | Make discount season-state-aware and confidence-weighted. |
| Two-for-one, consolidation, and liquidity constants | **Stop and review** | Useful but unsourced; high risk of false precision. | Ship as conservative defaults, flagged heuristic, or postpone. |
| Forced-release owner-behavior coefficients | **Reject / display-only for V1** | Too dependent on unsourced local behavior. | Use scenario notes and target tiers before scoring them. |
| Manual direct edits to final scores | **Reject** | Violates deterministic and explainable design. | Allow overrides only to inputs, assumptions, and provenance. |
| Generated outputs committed as fixtures | **Reject** | Encourages hand-editing results instead of recomputation. | Commit raw inputs, registries, and notes; generate outputs locally. |
| Confidence score using completeness, freshness, agreement | **Accept as-is, but label heuristic** | Strong rationale from source-reliability and forecast-combination research; exact weights still heuristic. citeturn6view11turn22view1 | Keep, and flag coefficient provenance clearly. |

## Final model-policy recommendations

### Veteran scoring

**Evidence-backed policy:** veteran scoring should be built primarily from **scoring-adjusted projection**, **replacement context**, **role certainty**, **position-specific age/risk bands**, and **injury/durability state**. That is the most defensible synthesis of the evidence you actually have. Replacement-level thinking is strongly supported; projections are more appropriate than rankings for custom scoring; and injury handling should be specific to type and position rather than generic. citeturn6view1turn6view6turn12search4turn13search0

**Model-design policy:** `veteran_base_value` should **not** directly include public market rank, headline contract size, or raw depth-chart slot. In LVE, first-down scoring should matter, but mostly through how it changes the player’s projection or as a small league-fit residual. The cleanest design is to convert projected usage into projected LVE fantasy output first, then add small overlays for replacement, age/durability, and declaration-window context. Public market value should live in `trade_liquidity_value`, not in the underlying private score.

### Asset conversion

**Evidence-backed policy:** any unified asset scale should be grounded in **replacement-aware projected contribution**, not in rank alone. Different roster settings alter the replacement baseline, which means asset conversion has to remain contextual. citeturn6view1turn14search0

**Model-design policy:** do not trust a single universal `all_asset_value` number by itself. Keep at least two visible companion numbers on every board:

- **Private roster value**: what this asset is worth to an LVE team under LVE scoring and replacement.
- **Trade liquidity value**: how easy the asset is to move in the public or semi-public dynasty market.

Then let `all_asset_value` be a **decision-layer composite**, not a hidden global truth. Future picks should be discounted by **time**, **uncertainty**, and **expected declaration-window veteran supply**, not by one fixed annual haircut.

### Forced-release strategy

**Evidence-backed policy:** there is no strong public evidence base for exact owner-behavior coefficients, reacquisition probabilities, or declaration-trade urgency percentages. This is the most league-specific and least externally validated part of the entire framework.

**Model-design policy:** Phase 8 should be implemented as a **strategy layer**, not as a hard production-value layer. Use official league rank only for **forced-release eligibility**, never as a direct player-value feature. Use opponent release models as **target bands** or **priority tiers**, not as faux-precise point estimates. In practical terms, `forced_release_pressure_score`, `pre_declaration_trade_urgency`, and `opponent_release_target_score` should be confidence-aware and visually caveated from day one.

### Source confidence

**Evidence-backed policy:** the hierarchy should prefer sources that are either official, scoring-convertible, or demonstrably more reliable for forecasting. Official injury reports are structured and specific; public consensus systems are real market signals but live in half-PPR frameworks; and forecast-combination research strongly favors combining diverse sources rather than picking one “best” source. citeturn18view0turn21view0turn21view1turn6view11turn22view1

**Model-design policy:** use this hierarchy for numeric value generation:

1. **Local scoring-adjusted projections** derived from vetted imported sources.
2. **Official league documents and official exported league state** for roster/pick/release eligibility.
3. **Official injury reports** for current availability.
4. **Consensus market ranks** for trade liquidity, never core private value.
5. **Contract sites** as secondary security context.
6. **Team depth charts** as weak role hints only.
7. **Manual notes/handwritten history** as provenance-rich qualitative context.

Confidence should rise with **completeness**, **freshness**, and **source agreement**, and fall with **missing data**, **low-tier sources**, and **manual overrides** unless those overrides replace obviously erroneous low-tier data with a higher-tier verified source.

### Manual overrides

**Evidence-backed policy:** none of the external literature supports silently hand-editing outputs. Forecast-combination literature supports transparent combination rules; it does not support opaque overrides. citeturn6view11turn22view1

**Model-design policy:** allow overrides only at the level of:

- source selection,
- raw input value,
- normalization bin,
- injury classification,
- league-state assumption,
- declaration/release status,
- projection-source inclusion.

Do **not** allow direct overrides to:

- `veteran_base_value`,
- `all_asset_value`,
- `trade_value`,
- `keeper_score`,
- `final_decision_score`.

Every override should require:
- author,
- timestamp,
- affected fields,
- reason,
- source or justification,
- review date/expiry,
- before/after values.

## Final do-not-implement list

Do **not** implement any of the following before coding changes go live:

- Do not use public expert ranks as a direct core scoring input for LVE veterans or assets. Those ecosystems are not built for no-PPR plus 0.4 rushing/receiving first-down scoring. citeturn21view0turn21view1turn6view6
- Do not use a single replacement threshold across normal dynasty play and the post-declaration offline draft.
- Do not score team depth-chart slot as if it were an official, reliable measure of role certainty. Team depth charts are often explicitly unofficial. citeturn6view8turn19view0
- Do not score contract headline dollars or “guaranteed” labels directly as production or keeper value. Guarantees are too nuanced. citeturn6view10
- Do not hard-code exact age cliffs by position as if they are strongly sourced truths.
- Do not assign a large standalone first-down weight on top of projections/role features without testing for double counting.
- Do not use fixed global future-pick discounts, two-for-one penalties, consolidation premiums, or liquidity penalties without calling them heuristics.
- Do not make owner-behavior or reacquisition formulas core numeric inputs before you have enough LVE history to calibrate them.
- Do not allow manual edits to final scores.
- Do not commit generated output tables as source-of-truth fixtures.
- Do not let QB or TE suppression become hard bans that block elite outliers or declaration-window bargains from surfacing.
- Do not make money decisions when the recommended move depends mainly on low-confidence market assumptions, unofficial depth-chart information, or owner-behavior heuristics.

## Final acceptance criteria before the app is decision-ready

The app should not be treated as decision-ready for money decisions until all of the following are true:

- Every core numeric input used in veteran scoring and asset conversion has explicit provenance.
- Every coefficient is tagged as either **evidence-backed direction** or **model-design heuristic**.
- The model separately computes **private roster value**, **trade liquidity value**, and **replacement context** rather than burying all three in one black box.
- The app has distinct tested behavior for **steady-state** and **declaration-window** replacement thresholds.
- Official injury reports outrank market blurbs and unofficial depth charts in the scoring pipeline. citeturn18view0turn6view8turn19view0
- Rankings are never used where scoring-adjusted projections are available. citeturn6view6turn21view0turn21view1
- Market ranks affect **liquidity/trade views** only, not core roster value.
- Contract and depth-chart features are capped as secondary modifiers or display-only cues.
- Manual overrides are limited to inputs/assumptions and are fully logged with before/after values.
- Deterministic tests exist for replacement-state switching, soft QB/TE suppression, missing-data penalties, confidence-score math, override logging, and audit-table contribution integrity.
- The forced-release module is clearly labeled as **strategy guidance with uncertainty**, not false-precision certainty.
- You have completed at least one local backtest or paper replay over prior LVE offseason decisions, especially around declaration and offline draft decisions, even if part of the history comes from handwritten records.
- Any recommendation with low confidence, missing core inputs, or heavy reliance on owner-behavior estimates is automatically marked **review required**.
- A human-readable audit table can explain why Asset A beat Asset B without requiring the user to trust a hidden coefficient stack.

The bottom line is straightforward. **Implement the framework, but downgrade the certainty.** The strongest parts of Phases 6–9 are the private-vs-market split, replacement-aware valuation, scoring-specific projections, official-source hierarchy, and deterministic auditability. The weakest parts are exact conversion constants, hard gates, depth-chart scoring, contract simplifications, and any precise owner-behavior math around forced releases. Those weak parts should either be postponed, visibly labeled heuristic, or made display-only until you have enough local LVE history to justify them.