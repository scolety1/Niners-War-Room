# Model v4.3.4 Historical Rookie Tuning Pro Audit Prompt

Please audit the attached Model v4.3.4 historical rookie tuning packet for a 10-team, 1QB, non-PPR dynasty league with first-down scoring and no TE premium.

The owner is concerned that the rookie model may not work because early historical hit rates looked low. A follow-up repair found that the first tuning tab was under-labeled: the project already had local RotoWire stat exports from 2021-2025, and those have now been used to create display-only outcome labels.

Please be brutally honest, but separate these possibilities:

1. the rookie formula is fundamentally bad,
2. the historical outcome labels are incomplete or not joined broadly enough,
3. the replay table is evaluating too broad a universe versus the actual fantasy rookie draft pool,
4. the scoring/output definition of "hit" is too strict or too noisy,
5. the model has useful signal but needs calibration around draft capital, production/team share, TE/QB positional discipline, or confidence caps.

## Context

Current Model v4.3.3/v4.3.4 constraints:

- Do not tune to consensus rankings just to match market.
- Weird model edges are allowed if evidence supports them.
- Market/ADP/ranking/projection/mock/big-board data must not drive private value.
- Outcomes must be display-only in historical replay and must not feed ranking.
- Missing data remains missing.
- Current outputs are review-only and must not mutate active rankings, My Team, War Board, readiness gates, or app promotion.

Current outcome-label state:

- Historical replay universe: 395 offensive rookie rows from 2021-2025.
- Outcome labels loaded: 338 rows.
- Outcome source: local RotoWire player stat intake, seasons 2021-2025.
- Outcome labels are joined after scoring and are display-only.
- Unloaded outcomes are missing labels, not automatic misses.
- 2025 outcomes are immature and should be treated as rookie-year-only context.

Current replay-judgment repair:

- The replay now separates `all_offensive_drafted` from `fantasy_relevant_replay_pool`.
- The replay now separates broad hits from strict starter hits and difference-maker hits.
- Outcome maturity is exposed so 2024 partial outcomes and 2025 rookie-year-only outcomes are not treated as final truth.
- These replay filters are evaluation-only. They do not affect model scores.

## Audit Questions

1. Is the historical replay implementation valid enough to judge formula quality?
2. Are the RotoWire-derived outcome labels complete enough for 2021-2025? If not, what conclusions are unsafe?
3. Are the hit rates actually low after accounting for partial outcome coverage?
4. Is the replay ranking the correct player universe for a fantasy rookie draft, or is it including too many NFL-drafted but fantasy-irrelevant players?
5. Does the model overvalue production/College Team Share relative to NFL Draft Pick Signal?
6. Does the model underweight first-round draft capital for WRs like Carnell Tate-style profiles?
7. Does the model overpromote late-capital high-production WR/RB profiles like Skyler Bell-style profiles?
8. Are TE values still too high for no TE premium?
9. Are QBs correctly discounted for 10-team 1QB?
10. Are confidence caps doing enough when evidence is partial, source-limited, or missing?
11. Should tuning be attempted now, or should outcome coverage/backtest design be repaired first?
12. If tuning is warranted, what specific formula changes should be tested without consensus-copying?

## Named Historical Sanity Checks

Please inspect whether the model behavior makes sense on historical examples, especially:

- Ja'Marr Chase
- DeVonta Smith
- Najee Harris
- Travis Etienne
- Kadarius Toney
- Breece Hall
- Garrett Wilson
- Drake London
- Treylon Burks
- Jahan Dotson
- Skyy Moore
- George Pickens
- Rachaad White
- Bijan Robinson
- Jahmyr Gibbs
- Zay Flowers
- Jaxon Smith-Njigba
- De'Von Achane
- Marvin Harrison Jr.
- Malik Nabers
- Rome Odunze
- Brock Bowers

## Required Verdict

Return one of:

- model likely viable, backtest/outcome coverage needs repair before tuning
- model viable but needs targeted formula calibration
- model not reliable for rookie drafting without major rebuild
- inconclusive because historical outcome data is insufficient

Please include:

- critical blockers
- high-priority issues
- medium/low issues
- specific examples
- whether to continue, pause, or bail
- the next 3 concrete actions

Do not recommend matching consensus rankings unless the evidence shows the model is unsupported.
