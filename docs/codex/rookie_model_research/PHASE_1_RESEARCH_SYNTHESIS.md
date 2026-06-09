# Deterministic Rookie Evaluation Research for the LVE Dynasty League

## League translation

Your league settings create a very specific rookie-evaluation environment, and that should materially change the model you build.

Because this is a 10-team, 1QB dynasty/keeper league with three starting WRs, two additional flex spots, no PPR, a 0.4 rushing/receiving first-down bonus, deep benches, and up to 23 protected players beginning in 2026, the model should not be optimized for generic dynasty rookie ADP. It should instead answer a narrower question: **which prospects most likely produce value in this exact scoring and roster ecosystem, relative to both rookies and the unusual veteran/free-agent pool created by the forced top-five release rule.**

That has several direct implications. First, quarterback scarcity is materially lower than in Superflex, and 3-point passing TDs further reduce the relative value of pure pocket passers compared with rushing QBs. Second, the lineup structure raises WR/RB demand much more than TE demand, because you can start three WRs and then fill two more flex spots with WR/RB/TE. Third, no PPR means you should care less about empty catch volume and more about yardage, touchdowns, first downs, and durable route/touch roles. Fourth, the first-down bonus specifically rewards players who stay on the field, earn meaningful touches, and convert them into chain-moving plays; that matters more for early-down RBs, efficient WRs, and route-earning TEs than it would in a generic full-PPR model. Fifth, deep benches and high keeper counts increase the value of patience, but the forced-release rule raises the opportunity cost of low-probability rookie stashes because released veterans may be better immediate assets than marginal rookies.

The right implementation is therefore **two-dimensional**, not one-dimensional: a **Talent Translation Score** for long-term NFL/fantasy success, and a separate **LVE Utility Score** for near-term fit in your format. Then, for every rookie pick, compare that rookie’s combined score against the best released veteran/free-agent alternatives likely to be available in your offline draft. That comparison step is crucial in LVE and is one of the biggest reasons generic rookie rankings will mislead you here.

## What the evidence actually supports

The strongest cross-position finding is that **NFL draft capital matters a lot**, but it matters for more than one reason. Earlier draft position generally correlates with better NFL outcomes for quarterbacks and wide receivers, and broad offensive-skill research finds that NFL teams are directionally good—but far from perfect—at identifying future productivity. At the same time, multiple studies show that the traits moving a player up draft boards are not always the same traits that best predict future NFL performance, especially at QB, WR, and TE. In other words, draft capital is useful because it captures private scouting information, medical/background vetting, and team willingness to create opportunity; it is not a pure measure of underlying talent. citeturn30search3turn39view0turn24view0turn11view0turn8view0

That distinction matters even more in fantasy. Fantasy-specific draft-capital research shows that early draft capital strongly drives **opportunity**, especially for RBs and QBs and, to a lesser degree, WRs and TEs. But those studies are mostly based on PPR-style outcomes, so in your league draft-capital hit rates should be treated as **directional**, not literal. Draft capital remains a core input, but the non-PPR plus first-down format means you should discount players whose likely fantasy path is mostly reception accumulation rather than efficient yardage, touchdown, and chain-moving usage. citeturn35view0

The second major cross-position finding is that **college production usually outperforms raw combine data**, but the best production variables are position-specific. For WRs and TEs, college receiving production and certain efficiency measures often matter more than the headline combine workout. For QBs, passing efficiency is important for getting drafted, but rushing ability is unusually important for actual NFL success once the QB has already cleared the “good enough passer to be drafted” threshold. For RBs, the combine matters more than at some other skill positions—especially speed and explosion—but still works best as a complement to production and receiving-role evidence, not a standalone filter. citeturn24view0turn11view0turn12view0turn9view3turn18view1turn37view0

The third cross-position finding is that **combine metrics are usually secondary, not primary**. Large-sample public work from entity["company","Pro Football Focus","football analytics company"] found only modest college-to-pro predictive power from height/weight/combine clusters for pass catchers overall, and broader strength-and-conditioning literature repeatedly characterizes combine tests as modest predictors whose usefulness varies a lot by position. The most consistent offensive signals are stronger for RB speed/explosion and specific TE/WR jump measurements than for most other flashy testing numbers. citeturn15view0turn18view1turn19search0turn37view0

The most important “mixed evidence” area is **age, early-declare status, breakout age, and age-adjusted production**. These are heavily used in public dynasty models, and there is substantial industry backtesting support for them, especially at WR and, to a lesser extent, RB. But the public peer-reviewed literature is thinner here than it is for draft capital, raw production, or some combine measures. So these variables should be used, but with honest humility: strong enough for meaningful weighting, not strong enough to override draft capital and core production by themselves. citeturn21search14turn22search6turn22search2turn21search18

The bottom-line modeling rule is simple: **use draft capital as the strongest single prior, use position-specific college production/efficiency as the main translation engine, use landing spot mostly for rookie-year utility, and use athletic testing as a secondary lens unless the position-specific evidence is stronger.**

## Quarterbacks

For LVE, quarterback is the easiest position to misprice. In a 1QB league with only 10 teams and 3-point passing TDs, rookie quarterbacks should be treated as **luxury assets**, not default targets. Only QBs with a strong combination of draft capital, rushing profile, and sack-avoidance/process traits should compete with top rookie RB/WR options or strong released veterans.

**Evidence-backed summary for LVE:** among QBs who are good enough passers to get drafted, college rushing ability is one of the clearest predictors of NFL success in public research, and fantasy scoring makes that even more powerful in your format. Meanwhile, draft capital matters because it buys patience and starting opportunity. Pocket-passing volume alone is not enough. citeturn24view0turn35view0

**Expert/industry overlay:** pressure handling, especially pressure-to-sack rate, scramble efficiency, and turnover-worthy play avoidance, appears genuinely useful for fantasy stability, but the strongest public evidence here comes more from industry analysis than peer-reviewed research. I would still use it. citeturn26view0turn26view1turn27search8

1. **Draft capital and organizational runway**  
   **Why it matters:** draft capital is both a talent prior and an opportunity prior. NFL teams give highly drafted QBs more chances, more patience, and more early starts. In fantasy, that matters even in 1QB because trade value and start probability are both heavily capital-dependent.  
   **Evidence:** High.  
   **Best for:** rookie-year production, trade value, long-term dynasty value.  
   **Recommended LVE weight:** **20%–30%**.  
   **Use as:** **core input**.  
   **Failure modes:** draft capital can overrate traits teams like for real football but that do not maximize fantasy in 1QB; it can also understate rushing upside when scouts lag behind. citeturn30search3turn39view0turn35view0

2. **Rushing and scrambling profile**  
   **Why it matters:** public econometric work finds that, among drafted QBs, college rushing is more strongly tied to NFL success than college passing variation, and scouts appear to undervalue it. In your league, rushing is even more valuable because passing TDs are worth only 3 points.  
   **Evidence:** High for NFL success; very high for fantasy translation.  
   **Best for:** fantasy success, rookie-year spike weeks, long-term ceiling.  
   **Recommended LVE weight:** **25%–35%**.  
   **Use as:** **core input** and **upside flag**.  
   **Failure modes:** some college runners are not functional NFL passers; the rushing trait should not override poor draft capital or bad passing/process markers. citeturn24view0

3. **Passing efficiency and accuracy in context**  
   **Why it matters:** models such as QBASE-style systems emphasize completion percentage, yards per attempt, team pass efficiency, experience, and opponent/teammate context for a reason. Passing efficiency helps get QBs drafted, and higher college QBR is positively associated with NFL QBR even if rushing carries more signal after selection.  
   **Evidence:** Medium-high.  
   **Best for:** real NFL success, base fantasy floor, trade value.  
   **Recommended LVE weight:** **15%–20%**.  
   **Use as:** **core input**.  
   **Failure modes:** raw passing yards, empty screen-game completion percentage, and scheme-inflated efficiency can all overstate NFL readiness. citeturn24view0turn23search8

4. **Sack avoidance and pressure-to-sack rate**  
   **Why it matters:** quarterbacks carry a lot of their own sack profile, and public fantasy/industry work argues that college pressure-to-sack rate is more useful as a “land mine detector” than as a star finder. QBs who habitually turn pressure into sacks kill drives and fantasy volume.  
   **Evidence:** Medium.  
   **Best for:** rookie-year stability, real NFL survivability, fantasy floor.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **risk flag** and **secondary input**.  
   **Failure modes:** exceptionally talented outliers exist; this is more powerful as a bust-prevention variable than as a ceiling variable. citeturn26view1turn26view0

5. **Play-level passing quality such as passing grade, big-time throws, and turnover-worthy plays**  
   **Why it matters:** play-by-play grading can capture traits that box scores miss. Public PFF work found college passing grade per snap had a meaningful correlation with NFL passing grade, and PFF’s BTT/TWP framework aims to isolate high-value throws and dangerous decisions better than touchdowns/interceptions alone.  
   **Evidence:** Medium.  
   **Best for:** real NFL success, fantasy stability, tie-breaking among similarly drafted QBs.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **secondary input** and **confidence modifier**.  
   **Failure modes:** public samples are smaller than ideal, and these measures should not overpower draft capital plus rushing. citeturn27search2turn27search0turn27search8

6. **Landing spot and immediate path to snaps**  
   **Why it matters:** in 1QB, the only rookie QBs worth prioritizing are the ones whose talent plus likely path to an NFL starting role justify occupying a protected roster slot.  
   **Evidence:** Medium for rookie-year value; lower for long-term intrinsic talent.  
   **Best for:** rookie-year fantasy and trade value.  
   **Recommended LVE weight:** **5%–10%**.  
   **Use as:** **confidence modifier**.  
   **Failure modes:** landing spot is fragile and can change quickly with coaching/line play; do not let it overwhelm the pre-draft profile. citeturn35view0turn26view0

**What not to overweight at QB:** raw passing yards, college wins, school brand, pro-day narratives, hand size, or 40 time without meaningful rushing production. Also do not overpay for “safe” older pocket passers in 1QB unless both draft capital and sack/process indicators are strong. The scoring system and roster format do not reward that archetype enough. citeturn24view0turn18view1turn35view0

## Running backs

RB is where your scoring and lineup settings most sharply differ from generic dynasty models. No PPR reduces the standalone value of checkdown volume, but the first-down bonus and 4-point rushing/receiving TDs strongly reward backs who stay on the field, earn meaningful touch share, and handle scoring/chain-moving work. In this format, **role quality** matters more than raw reception count.

**Evidence-backed summary for LVE:** draft capital is the strongest single predictor of early fantasy usefulness at RB because it drives opportunity; college receiving performance also carries non-trivial signal; among combine metrics, RB speed/explosion has more support than most offensive positions. citeturn35view0turn15view0turn18view1turn37view0

**Expert/industry overlay:** public dynasty modeling increasingly treats receiving usage, route share, and touches-per-snap or touches-per-team-play as highly predictive. I agree with using those, but the academic/public-journal evidence is thinner than for draft capital and basic athletic translation. In your league I would emphasize **receiving role quality**, not just raw catches. citeturn15view0turn36search0

1. **Draft capital and expected touch runway**  
   **Why it matters:** this is the clearest opportunity variable at RB. Fantasy-specific research shows first-round RBs dramatically outproduce later-round backs in early-career opportunity and hit rates, and public academic work consistently finds stronger RB translation from draft-relevant traits than at some other offensive positions.  
   **Evidence:** High.  
   **Best for:** rookie-year fantasy, trade value, long-term dynasty value.  
   **Recommended LVE weight:** **25%–35%**.  
   **Use as:** **core input**.  
   **Failure modes:** RB draft classes are volatile; late-round backs can emerge if depth charts break right, but the base rate is much worse. In LVE, that matters because released veterans may be stronger bets than thin Day 3 RBs. citeturn35view0turn18view1turn19search19

2. **Receiving usage and route-earning ability**  
   **Why it matters:** for RBs, college receiving grades and per-route metrics translate better from college to the pros than they do for WRs or TEs. That does not mean you should chase empty catches in a non-PPR league; it means you should favor backs who can earn routes, stay on the field, and convert passing-game work into first downs and total touches.  
   **Evidence:** Medium-high.  
   **Best for:** rookie-year fantasy, long-term three-down value, floor.  
   **Recommended LVE weight:** **15%–20%**.  
   **Use as:** **core input**.  
   **Failure modes:** satellite backs without goal-line/early-down access lose value in your format relative to PPR leagues. citeturn15view0

3. **Explosive athleticism, especially 40-yard dash and broad/long jump**  
   **Why it matters:** RB is one of the few offensive positions where faster timed speed and explosion show more repeatable predictive value. Studies found 40 time and standing long jump were predictive of rushing output, while later literature reviews also identify faster 40s and longer broad jumps as recurring signals for RB performance and longevity.  
   **Evidence:** Medium-high.  
   **Best for:** real NFL success, home-run fantasy upside, long-term ceiling.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **secondary input** and **upside flag**.  
   **Failure modes:** pure straight-line speed without vision, contact balance, or receiving role can still bust; athleticism should refine draft-capital tiers, not replace them. citeturn18view1turn19search19turn37view0

4. **Size/BMI and speed-score style build checks**  
   **Why it matters:** public research is not unanimous, but multiple studies and literature reviews find that bigger RBs with stronger speed profiles tend to translate better, especially when the size is functional and paired with real speed. In LVE, that matters because short-yardage and first-down work have extra value.  
   **Evidence:** Medium.  
   **Best for:** fantasy floor, durability, goal-line/first-down projection.  
   **Recommended LVE weight:** **8%–12%**.  
   **Use as:** **floor flag** and **confidence modifier**.  
   **Failure modes:** do not turn BMI into a hard cutoff; some elite lighter backs exist, and size without receiving skill or burst can still disappoint. citeturn37view0turn36search8turn36search3

5. **Age, early-career production, and early declare signal**  
   **Why it matters:** the public fantasy community has found meaningful signal in early-career production and experience-adjusted RB output, but the strongest support here comes from industry backtests, not deep peer-reviewed literature. Still, younger productive backs generally deserve credit.  
   **Evidence:** Medium-low.  
   **Best for:** long-term dynasty value, tie-breaking within tiers.  
   **Recommended LVE weight:** **5%–10%**.  
   **Use as:** **secondary input** and **tiebreaker**.  
   **Failure modes:** COVID eligibility, transfers, committee usage, and school context can all muddy age-based readings. citeturn22search2turn21search18

6. **Short-yardage, goal-line, and first-down role projection**  
   **Why it matters:** this is the most LVE-specific RB variable. There is not strong public literature directly on college first-down profiles translating to NFL fantasy first-down bonuses, so this should be treated as a model-design inference rather than a proven coefficient. But in your scoring, backs likely to handle chain-moving early downs and scoring carries deserve a meaningful bump.  
   **Evidence:** Low for direct prospect prediction; strong league-fit logic.  
   **Best for:** rookie-year fantasy, weekly floor, contender builds.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **LVE overlay**, **floor flag**, and **upside flag** when paired with receiving work.  
   **Failure modes:** projection errors are common because NFL coaching usage is hard to know pre-draft; keep this separate from the core pre-draft talent score.  

**What not to overweight at RB:** raw college carry totals, raw yards per carry without market/context, pure receiving totals stripped from route share or touch quality, bench press, or late-round “good landing spot” backs with weak talent profiles. In LVE, the release rule makes it easier to take productive veterans instead of forcing a Day 3 rookie stash. citeturn35view0turn18view1turn37view0

## Wide receivers

Receiver is the most important long-term rookie stash position in your format because you must start three WRs and can start even more in flex. But your scoring is not full PPR, so the model should prefer **yardage creation, target earning, touchdowns, and first-down efficiency** over pure catch volume.

**Evidence-backed summary for LVE:** draft capital and college production matter a lot; college stats generally beat combine metrics for predicting NFL receiving performance; per-route efficiency and play-level receiving quality add signal, though their college-to-pro translation is imperfect; combine testing is useful, but should usually be secondary. citeturn11view0turn12view0turn15view0turn37view0

**Expert/industry overlay:** breakout age, early declare, weighted breakout age, YPTPA, and age-adjusted market-share metrics are very common in WR models for a reason, but their public support is more backtest-heavy than journal-heavy. I would absolutely use them, but below draft capital and core production. citeturn21search14turn22search6turn21search18

1. **Draft capital**  
   **Why it matters:** earlier-drafted WRs are more likely to receive early opportunity and to produce better NFL outcomes than later-drafted WRs, even though the first round is not a guarantee and later-round outliers do exist. In fantasy, draft capital also strongly affects immediate market value.  
   **Evidence:** High.  
   **Best for:** rookie-year production, trade value, long-term dynasty value.  
   **Recommended LVE weight:** **20%–30%**.  
   **Use as:** **core input**.  
   **Failure modes:** some of the traits teams reward on draft day are not the traits that best drive downstream production; draft capital should anchor the model, not end the discussion. citeturn30search3turn39view0turn35view0turn11view0turn12view0

2. **College receiving production in context**  
   **Why it matters:** college production repeatedly beats raw combine data in WR research. The most useful inputs are not just raw counting stats, but share and context: dominator-style market share, receiving yards share, target share where available, and production that was achieved without needing to be an old player beating younger competition.  
   **Evidence:** Medium-high overall; medium for age-adjusted variants specifically.  
   **Best for:** real NFL success, long-term dynasty value, trade insulation.  
   **Recommended LVE weight:** **20%–30%**.  
   **Use as:** **core input**.  
   **Failure modes:** scheme inflation is real; final-year-only explosions from very old prospects deserve skepticism. citeturn11view0turn12view0turn21search18turn21search14turn22search6

3. **Per-route earning and efficiency metrics such as YPRR, TPRR, and receiving grade per route**  
   **Why it matters:** these metrics capture whether the WR actually earns targets and turns routes into yards, which is more useful for your format than simple catch totals. Public PFF work found college receiving grade per route had modest college-to-pro correlation and that raw YPRR translation is weaker than many people assume, but YPRR remains a useful descriptive-plus-predictive input when interpreted with context.  
   **Evidence:** Medium.  
   **Best for:** NFL receiving talent, fantasy ceiling, tie-breaking among similarly drafted WRs.  
   **Recommended LVE weight:** **15%–20%**.  
   **Use as:** **secondary input** and **confidence modifier**.  
   **Failure modes:** YPRR can be biased by personnel usage and offensive environment; it should be adjusted mentally for scheme and route competition and should not be used in isolation. citeturn15view0turn15view1turn15view2

4. **Touchdown share, chain-moving profile, and quality of targets**  
   **Why it matters:** this is more valuable in LVE than in PPR. Older public WR work found college TD production and final-year yard share more predictive than some headline combine traits, and no-PPR plus first-down scoring increases the value of WRs who turn targets into meaningful yards, scores, and first downs rather than just short catches.  
   **Evidence:** Medium.  
   **Best for:** rookie-year fantasy and format-specific ceiling.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **LVE overlay**, **upside flag**, and **secondary input**.  
   **Failure modes:** touchdown rates are noisy; treat them as part of a broader efficiency/role cluster, not a standalone driver. citeturn11view0turn13view3

5. **Athletic explosiveness, especially vertical and 40 time**  
   **Why it matters:** WR testing is not meaningless, but public work suggests it is often less important than people think once real production is in view. The most consistent signals are speed for draft position and some evidence for vertical/athletic explosion relating to NFL performance.  
   **Evidence:** Medium.  
   **Best for:** ceiling, archetype mapping, tie-breaking.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **secondary input** and **upside flag**.  
   **Failure modes:** do not let 40 time or RAS-style composites overtake draft capital plus strong production. Many fast WRs fail because they never become real target earners. citeturn12view0turn13view2turn37view0

6. **Landing spot, target competition, and QB environment**  
   **Why it matters:** landing spot is not the same as talent, but it absolutely changes rookie-year utility. Prior WR research summarized in later work found rookie receptions and starts were affected by team competition and surrounding offensive quality.  
   **Evidence:** Medium for rookie-year production; lower for long-term true talent.  
   **Best for:** rookie-year fantasy and trade value.  
   **Recommended LVE weight:** **8%–12%**.  
   **Use as:** **confidence modifier**.  
   **Failure modes:** situations change quickly; do not let a clean depth chart rescue a bad prospect. citeturn12view0

7. **Return-game role**  
   **Why it matters:** in your scoring, return yards count. That means a WR with a plausible return role can produce usable spike weeks before earning a full offensive role.  
   **Evidence:** Low as a predictive indicator of long-term offensive success; strong as a league-specific scoring bonus.  
   **Best for:** rookie-year fantasy only.  
   **Recommended LVE weight:** **0%–5%**.  
   **Use as:** **tiebreaker** and **short-term upside flag**.  
   **Failure modes:** return roles are unstable and often disappear once offensive roles grow.  

**What not to overweight at WR:** raw receptions, slot volume by itself, late declare “breakout” seniors, pure contested-catch narratives without route-earning evidence, or straight-line speed detached from production. In your format a WR who catches 85 short balls but does not earn first downs or score much is materially less useful than in full PPR. citeturn15view0turn15view2turn11view0

## Tight ends

TE should be valued the most carefully in this league. You start only one, there is no TE premium, and rookie TEs are usually slow burns. That makes TE the position where **generic dynasty enthusiasm most often overstates actual LVE value**.

**Evidence-backed summary for LVE:** TE draft capital matters, but less cleanly than at RB or QB; college receiving production and specific athletic markers—especially broad jump and speed—show stronger public evidence than TE size or bench strength alone; there are meaningful later-round outliers, which lowers the value of paying full rookie price. citeturn8view0turn9view3turn35view0turn37view0

**Expert/industry overlay:** public TE prospect work increasingly emphasizes YAC, tackle-breaking, short-area speed, and whether the player is truly a receiving TE instead of a blocking-first TE. I think that is directionally right, but the public sample is much smaller than at WR/RB, so the model should be humble and avoid overfitting. citeturn29view0

1. **Draft capital**  
   **Why it matters:** draft capital still matters for opportunity and trade value, but TE is one of the easiest positions for draft capital to mislead because later-round elite outcomes occur more often than at QB/RB.  
   **Evidence:** Medium-high.  
   **Best for:** rookie-year opportunity, trade value, baseline dynasty value.  
   **Recommended LVE weight:** **18%–25%**.  
   **Use as:** **core input**.  
   **Failure modes:** do not treat first-round TE capital the way you treat first-round RB capital; the payoff curve is much less reliable. citeturn35view0turn29view0

2. **College receiving production and market-share style usage**  
   **Why it matters:** the strongest peer-reviewed TE work found NFL performance was better predicted by college receptions/yards variables and broad-jump/explosion variables than by the traits dominating draft order. Final-year receiving share and overall college receiving output were especially important.  
   **Evidence:** High relative to TE literature.  
   **Best for:** real NFL success, long-term fantasy value.  
   **Recommended LVE weight:** **20%–30%**.  
   **Use as:** **core input**.  
   **Failure modes:** TE college usage is scheme-sensitive and often under-represents real ability, so low volume is not always a death sentence—but high-quality receiving evidence is still a major positive. citeturn9view3turn9view0

3. **Explosive athleticism, especially broad jump and speed**  
   **Why it matters:** the TE literature repeatedly identifies broad jump and 40-yard dash as more relevant to NFL success than some more traditional “football strength” signals. Broad jump, in particular, showed up repeatedly as predictive of NFL TE performance even when it was not central to draft order.  
   **Evidence:** High relative to TE literature.  
   **Best for:** real NFL success, fantasy ceiling, late-round upside hunting.  
   **Recommended LVE weight:** **15%–20%**.  
   **Use as:** **core input** and **upside flag**.  
   **Failure modes:** pure athletes with little receiving role can still fail; athleticism must be paired with receiving evidence. citeturn9view3turn38view3turn37view0

4. **Receiving efficiency and after-catch traits**  
   **Why it matters:** industry work suggests useful TE signals live in YPRR, YAC per reception, and tackle-avoidance style traits because top NFL TEs create a large share of their value after the catch and underneath. In your format, that also maps well to first-down scoring.  
   **Evidence:** Medium.  
   **Best for:** fantasy upside, tie-breaking, stash selection.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **secondary input** and **upside flag**.  
   **Failure modes:** small TE samples mean volatility is high; use this to separate close TE prospects, not to crown one from scratch. citeturn29view0turn15view0

5. **Receiving role versus blocking-first role**  
   **Why it matters:** in a no-TE-premium league, you care far more about whether the TE can earn routes than whether he is a useful real-life blocker. Public research and analysis both imply that blocking-first archetypes are often overvalued by actual draft processes relative to fantasy usefulness.  
   **Evidence:** Medium-low publicly, but strategically very important.  
   **Best for:** rookie-year fantasy and long-term fantasy translation.  
   **Recommended LVE weight:** **10%–15%**.  
   **Use as:** **confidence modifier** and **risk flag**.  
   **Failure modes:** some players develop into two-way stars, but you should default toward route-earning evidence. citeturn29view0turn9view0

6. **Landing spot and patience horizon**  
   **Why it matters:** TE development is slower, and in your league released veterans will frequently be better short-term TE bets than rookies. The right use of a rookie TE is usually long-horizon bench protection, not immediate lineup expectation.  
   **Evidence:** Medium for rookie-year value; low for intrinsic talent.  
   **Best for:** rookie-year utility and roster construction.  
   **Recommended LVE weight:** **8%–12%**.  
   **Use as:** **LVE overlay** and **confidence modifier**.  
   **Failure modes:** a good-looking depth chart can tempt you into over-drafting middling prospects at the least scarce flex-eligible position in your format. citeturn35view0turn29view0

**What not to overweight at TE:** raw size, bench press, generic “mismatch” language, blocking reputation, or the assumption that every first-round TE is a future fantasy difference-maker. In LVE, most rookie TEs should be drafted only when the price is right or the profile is elite across receiving usage, capital, and explosion. citeturn9view0turn9view3turn29view0

## How I would build the model

Use a **position-specific deterministic model**, not one generic set of coefficients.

For each position, I would store every input in one of six buckets:

- **Core input**: strongest predictors with real weight.
- **Secondary input**: meaningful, but not strong enough to drive the model.
- **Confidence modifier**: changes certainty around the projection.
- **Risk flag**: bust land-mine variable.
- **Upside flag**: raises the ceiling without creating the floor.
- **LVE overlay/tiebreaker**: scoring- and roster-specific variable such as first-down role projection, return value, or immediate veteran competition.

Then produce four outputs for every player:

**Base Translation Score.** This should be mostly evidence-backed pre-draft signal: draft capital, position-specific production, and the strongest translation metrics.

**Opportunity/Market Score.** This should capture draft capital again, landing spot, depth chart path, and the likelihood the player gains value quickly in dynasty trade markets.

**LVE Utility Score.** This is your custom overlay for the actual league: no PPR, first-down bonus, 1QB, no TE premium, return yards, deep benches, released-veteran competition.

**Risk/Confidence Summary.** Keep this verbal and explainable: “strong draft capital but weak sack avoidance,” “great receiving TE profile but likely blocked for two years,” “Day 3 RB with receiving skill but poor first-down role projection,” and so on.

If you want one practical rule for rookie-vs-veteran decisions in LVE, it is this: **a non-elite rookie should usually lose to a strong released veteran unless the rookie clears at least one of the following bars**:

- strong draft capital,
- clear position-specific translation profile,
- unusually good LVE scoring fit,
- or meaningful long-term dynasty insulation.

That will save you from making “generic dynasty” picks that do not actually help in this specific league.

## Open questions and limitations

The strongest evidence in the public literature is on **draft capital, broad college production, some combine translation, and QB rushing**. The weakest evidence is on **first-down profile, targets per route run as a public prospect variable, missed tackles forced/YAC/contact metrics as long-horizon predictors, and some age-adjusted prospect measures outside industry backtests**. Where I recommend using those weaker variables, I am doing so as an explicit model-design choice, not claiming the public literature proves a precise coefficient. citeturn15view0turn21search14turn22search6turn29view0

A second limitation is that much of the fantasy-specific public research uses PPR-style outcomes. That means **your LVE league-adjustment layer matters a lot**. In particular, you should shade down pure reception volume, shade up first-down and touchdown role, and aggressively de-emphasize rookie QB and TE premiums that come from Superflex or TE-premium discourse. citeturn35view0

The third limitation is that some useful public metrics—especially play-level charting metrics from entity["organization","NCAA","college athletics governing body"] prospects and from advanced providers—are not always historically available in clean, complete datasets for every class. In a local-first tool, the right answer is not to ignore them; it is to record them as **secondary inputs with visible missingness**, so your model stays deterministic and explainable rather than pretending unavailable data were uniform across prospects.