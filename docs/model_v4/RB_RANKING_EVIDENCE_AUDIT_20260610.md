# RB Ranking Evidence Audit - 2026-06-10

## Scope

This is a research/audit pass only. It does not change production rankings, active `latest`, generated scoring outputs, formulas, or data packs.

The question is whether the active model is correctly ranking high RBs, especially James Cook and Josh Jacobs, for this league:

- 10-team dynasty/keeper.
- 1QB, no superflex.
- No PPR.
- No TE premium.
- Rushing/receiving first downs matter.
- 2 RB, 3 WR, 1 TE, 2 FLEX, 1 K.

Blocked inputs remain blocked from private scoring: ADP, market rank, public rankings, consensus, projections, trade calculators, league rank, RotoWire rankings/projections, prior draft history, and legacy active-pack private score.

## Data Sources Inspected

Active current board:

- `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- Active rows: `240`
- Scored QB/RB/WR/TE rows: `232`
- Unscored kickers: `8`

Active private component rows:

- `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv`

Historical/replay sources:

- `local_exports/model_v4/model_edge/latest/model_edge_evaluation_harness_review_rows.csv`
- `local_exports/model_v4/model_edge/latest/model_edge_evaluation_position_summary.csv`
- `local_exports/model_v4/model_edge/latest/shadow_model_tournament_historical_metrics.csv`
- `local_exports/model_v4/model_edge/latest/shadow_model_tournament_current_board_rows.csv`
- `local_exports/model_v4/audit_packets/model_v4_3_5_historical_replay_judgment_repair_audit_20260526/13_historical_rookie_backtest_feature_matrix.csv`
- `local_exports/model_v4/audit_packets/model_v4_3_5_historical_replay_judgment_repair_audit_20260526/10_historical_rookie_outcome_labels.csv`

Important limitation: the strongest outcome harness is a rookie replay/outcome harness from 2021-2025. It can test rookie RB profile families and early-career hit/bust patterns, but it cannot fully validate veteran retained-value decay for players like Josh Jacobs, Christian McCaffrey, Derrick Henry, Saquon Barkley, Tony Pollard, or Jaylen Warren.

## Component Table

| Player | Rank | Score | Age | Role/archetype | VORP | Review pts | 1D pts | Lifecycle | Conf | Key warnings | Read |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| Bijan Robinson | 3 | 78.4618 | 24.3 | short-window three-down | 174.0 | 309.6 | 38.8 | 1.04 | 0.88 | route/role evidence missing | Young elite multi-signal RB; model probably right. |
| Jonathan Taylor | 4 | 74.3080 | 27.3 | short-window three-down | 179.3 | 314.9 | 39.6 | 0.9776 | 0.88 | age after 27 active | Prime productive workhorse; still high but age caution is active. |
| Jahmyr Gibbs | 5 | 70.7273 | 24.1 | short-window three-down | 152.9 | 288.5 | 33.6 | 1.04 | 0.88 | route/role evidence missing | Young elite multi-signal RB; model probably right. |
| De'Von Achane | 9 | 61.3322 | 24.6 | short-window three-down | 127.8 | 263.4 | 31.6 | 1.04 | 0.88 | route/role evidence missing | High upside, but fragility should stay visible. |
| James Cook | 11 | 59.6640 | 26.6 | short-window rushing role | 140.2 | 275.8 | 31.6 | 0.99 | 0.88 | receiving-role fragility; route/role evidence missing | Strong current first-down/VORP case; rank may be too short-window heavy relative to WRs. |
| Kyren Williams | 15 | 53.9777 | 25.7 | short-window three-down | 97.6 | 233.2 | 29.6 | 1.04 | 0.82 | partial first-down cap; header cleanup warning | Useful but thinner/fragility profile; likely needs stronger confidence caution. |
| Christian McCaffrey | 18 | 53.0131 | 29.9 | short-window three-down | 192.6 | 328.2 | 47.6 | 0.6656 | 0.88 | RB age curve 30-plus; cliff guardrail | Score is still high because evidence is massive; age/horizon risk is real. |
| Chase Brown | 24 | 49.1893 | 26.1 | short-window three-down | 82.0 | 217.6 | 28.0 | 1.04 | 0.88 | route/role evidence missing | Late-capital hit profile, but top-24 is aggressive. |
| Breece Hall | 31 | 41.9244 | 24.9 | short-window three-down | 49.8 | 185.4 | 22.8 | 1.04 | 0.88 | partial first-down cap | Lower current component than intuition; may be too low if durable talent signal matters. |
| Josh Jacobs | 32 | 41.2427 | 28.2 | short-window three-down | 61.5 | 197.1 | 22.0 | 0.8944 | 0.88 | partial first-down; age after 27 active | Productive workhorse with active age penalty; not obviously egregious at 32. |
| Saquon Barkley | 38 | 38.0800 | 29.2 | short-window three-down | 59.9 | 195.5 | 19.2 | 0.7904 | 0.88 | age cliff guardrail; partial first-down | Model is already discounting age. |
| Travis Etienne | 41 | 36.3324 | 27.3 | short-window three-down | 75.5 | 211.1 | 19.2 | 0.9776 | 0.80 | no historical component; team/status warning; age caution | Source/data + age caution; probably too high until source is cleaner. |
| Jaylen Warren | 43 | 34.2024 | 27.5 | short-window rushing role | 58.3 | 193.9 | 26.0 | 0.9306 | 0.88 | no historical component; shifted header; age caution | Short-window role score may be too generous. |
| Derrick Henry | 65 | 28.3132 | 32.4 | short-window rushing role | 133.1 | 268.7 | 33.2 | 0.4554 | 0.88 | extreme RB age cliff | Age cliff is active; model probably right to lower him. |
| Kenneth Walker | 73 | 26.7476 | 25.6 | short-window rushing role | 38.5 | 174.1 | 23.2 | 0.99 | 0.80 | missing stats-first evidence; team/status warning | Source-limited; receiving fragility makes rank cautious. |
| Tony Pollard | 76 | 26.3285 | 29.0 | short-window three-down | 33.8 | 169.4 | 23.6 | 0.7904 | 0.88 | no historical component; age cliff | Model probably right to keep outside core tier. |
| Chuba Hubbard | 117 | 18.6020 | 26.9 | role fragility review | 0.0 | 113.4 | 17.2 | 0.8648 | 0.88 | no historical component; age window caution | Role/score correctly looks fragile. |
| Rachaad White | 127 | 16.8518 | 27.3 | role fragility review | 0.0 | 113.8 | 18.8 | 0.8648 | 0.80 | no historical component; team/status warning; age caution | Model probably right to discount. |

## Evidence Profile Buckets

### Young elite multi-signal RB

Players: Bijan Robinson, Jahmyr Gibbs.

These profiles have young age, very high private VORP/review points, imported first-down evidence, strong role label, and no age penalty. The historical rookie replay supports this family: early-capital RBs with rushing/receiving evidence were the cleanest RB profile in the available data.

Verdict: model probably right.

### Prime/near-prime productive workhorse with age-window caution

Players: Jonathan Taylor, Josh Jacobs, Saquon Barkley, Christian McCaffrey.

These players have real current production signals, but age/lifecycle penalties determine whether the dynasty horizon is believable. Taylor remains high because current evidence is extreme and lifecycle is only mildly discounted. Jacobs is much lower because age and lifecycle warnings are already active. CMC remains top-20 because evidence is massive despite a severe lifecycle penalty.

Verdict: mixed. Taylor/CMC are high because current evidence is overwhelming; Jacobs at 32 is defensible but should keep horizon warnings visible.

### Prime first-down / rushing-value short-window RB

Players: James Cook, Jaylen Warren, Derrick Henry, Kenneth Walker.

This bucket gets rewarded when imported first-down points and VORP are strong. Cook is the clearest high-value case here: 140.2 VORP, 275.8 review points, 31.6 first-down points, age 26.6. However, the role label is `rb_short_window_rushing_role_asset` rather than true durable receiving/three-down proof, and the fragility status says `rb_receiving_role_fragility_review`.

Verdict: Cook is not a fake signal, but the current rank may be overvaluing near-term first-down/VORP versus WR useful window.

### Young/prime short-window three-down RB

Players: De'Von Achane, Kyren Williams, Chase Brown, Breece Hall.

This bucket can create real edge, especially in first-down scoring, but it is also where short-window RB production can overpower dynasty horizon. Achane, Kyren, and Brown all have current evidence that matters. Brown also has a historical rookie hit receipt. Breece is the counterexample: strong original prospect profile but weaker current private component, so the active model is less enthusiastic.

Verdict: high variance. Needs separate upside vs fragility language, not a single hidden blended score.

### Source-limited / role-fragility RB

Players: Travis Etienne, Kenneth Walker, Rachaad White, Chuba Hubbard.

These rows carry no historical component/source warnings, team/status warnings, missing stats-first evidence, or role fragility. The model generally keeps them lower, but Etienne and Warren still rank high enough to deserve review.

Verdict: source/data issue plus possible formula issue for short-window role score.

## Historical Replay Findings

Available harness:

- 395 historical rookie replay rows.
- 105 RB rows.
- 61 mature RB rows with three-year windows.
- 90 RB rows with outcome labels loaded.

Position-level RB result:

- Mature RB strict starter hit rate: `0.230`.
- Mature RB difference-maker rate: `0.197`.
- Replacement/bust rows: `30`.
- Too early/missing rows: `52`.

Rank-window RB result from the shadow tournament baseline:

| Rank window | Rows | Strict hit rate | Difference-maker rate | Bust rate |
|---|---:|---:|---:|---:|
| RB top 12 | 13 | 0.615 | 0.615 | 0.077 |
| RB top 24 | 27 | 0.333 | 0.333 | 0.370 |
| RB top 36 | 34 | 0.324 | 0.324 | 0.382 |

Profile buckets from the rookie matrix:

| Rookie profile family | Rows | Strict 2+ starter seasons | Difference-maker rate | Useful rate | Read |
|---|---:|---:|---:|---:|---|
| Early-capital receiving+rushing profile | 7 | 0.714 | 0.714 | 1.000 | Strongest RB family. Includes James Cook's rookie class profile. |
| Early-capital rushing profile | 1 | 1.000 | 1.000 | 1.000 | Too small; Bijan-type profile. |
| Middle-capital receiving path | 4 | 0.750 | 0.750 | 1.000 | Small sample but very strong. Includes Achane/Rachaad-style hits. |
| Late-capital receiving path | 11 | 0.182 | 0.182 | 0.455 | Real hits exist, but false positives are common. |
| Late-capital rushing/opportunity | 31 | 0.000 | 0.032 | 0.194 | Most fragile profile family. |
| Middle-capital rushing profile | 4 | 0.000 | 0.000 | 0.000 | Very risky in available sample. |

Past examples from current watch names:

- James Cook: 2022, round 2 pick 63, historical rookie replay result `Difference-maker`.
- Bijan Robinson: 2023, round 1 pick 8, `Difference-maker`.
- Jahmyr Gibbs: 2023, round 1 pick 12, `Difference-maker`.
- De'Von Achane: 2023, round 3 pick 84, `Difference-maker`.
- Kyren Williams: 2022, round 5 pick 164, `Difference-maker`.
- Chase Brown: 2023, round 5 pick 163, `Difference-maker`.
- Breece Hall: 2022, round 2 pick 36, `Difference-maker`.
- Rachaad White: 2022, round 3 pick 91, `Difference-maker`.
- Kenneth Walker III: outcome missing in the harness.

Historical conclusion: the model is not crazy to value RBs highly in this format. RB top-12 rookie replay rows were strong, and first-down scoring can make high-touch RBs especially valuable. The risk starts when the model lets short-window role/VORP elevate RBs into dynasty WR territory without enough horizon/role durability separation.

## Prior RB Horizon Shadow Test

The previous shadow tournament included `rb_dynasty_horizon`. It was not promoted.

Historical result:

- Overall top-24 strict hit rate stayed `0.264`; bust rate stayed `0.389`.
- RB top-24 strict hit rate improved from `0.333` to `0.429`.
- RB top-24 bust rate improved from `0.370` to `0.238`.
- RB top-36 strict hit rate improved from `0.324` to `0.333`.
- RB top-36 bust rate improved from `0.382` to `0.364`.

Current-board movement was too blunt:

| Player | Active rank/score | RB horizon shadow | Score delta | Read |
|---|---:|---:|---:|---|
| James Cook | 11 / 59.664 | 10 / 57.664 | -2.0 | Mild discount only. |
| Josh Jacobs | 32 / 41.2427 | 41 / 33.2427 | -8.0 | Big age/horizon discount. |
| Bijan Robinson | 3 / 78.4618 | 3 / 77.4618 | -1.0 | Elite young RB mostly preserved. |
| Jahmyr Gibbs | 5 / 70.7273 | 6 / 69.7273 | -1.0 | Elite young RB mostly preserved. |
| Jonathan Taylor | 4 / 74.308 | 4 / 71.308 | -3.0 | Productive prime RB preserved. |
| De'Von Achane | 9 / 61.3322 | 12 / 56.3322 | -5.0 | Short-window cap. |
| Kyren Williams | 15 / 53.9777 | 25 / 46.9777 | -7.0 | Role/availability fragility. |
| Chase Brown | 24 / 49.1893 | 28 / 44.1893 | -5.0 | Short-window cap. |
| Breece Hall | 31 / 41.9244 | 36 / 36.9244 | -5.0 | Short-window cap. |
| Josh Jacobs | 32 / 41.2427 | 41 / 33.2427 | -8.0 | Age/lifecycle horizon discount. |

Read: the RB horizon idea has evidence behind it, but the existing implementation is too broad to promote. A v2 should be narrower and should separate upside/floor/fragility rather than just cutting scores.

## James Cook Deep Read

### What the model is seeing

- Active rank/score: `#11 / 59.664`.
- Age: `26.6`.
- Role: `rb_short_window_rushing_role_asset`.
- Fragility: `rb_receiving_role_fragility_review`.
- Private VORP: `140.2`.
- Review scoring points: `275.8`.
- First-down points: `31.6`.
- Lifecycle modifier: `0.99`.
- Confidence cap: `0.88`.
- Warnings: route/target/snap evidence missing, lifecycle/role evidence missing.
- Historical rookie replay: 2022 round 2 pick 63, classified as a `Difference-maker`.

### Is the evidence historically predictive?

Partly yes. Cook's original rookie profile falls in the early-capital receiving+rushing family, which was the strongest RB profile in the available rookie replay. He is also not an unsupported one-year, low-evidence player.

The caution is that the active current-value role label is not "durable receiving three-down cornerstone"; it is a short-window rushing role with receiving fragility. That means the current score may be blending near-term usefulness and dynasty horizon too tightly.

### Does first-down scoring matter?

Yes. Cook has strong imported first-down value (`31.6`). In this league, first downs are real scoring events and can make efficient high-touch backs more valuable than standard dynasty intuition would imply.

### What would make the model wrong?

- If current VORP is mostly a short-window role spike.
- If receiving/third-down work is not durable.
- If the model treats first-down production as horizon-stable without enough role security evidence.
- If WR opportunity cost is underweighted: Cook sits above Zay Flowers, A.J. Brown, Chris Olave, Nico Collins, Drake London, CeeDee Lamb, and Justin Jefferson despite a shorter expected RB window.

### Cook verdict

`inconclusive / leaning model probably too high`

Do not hard-cut him from current evidence. The model has real support. But #11 overall is aggressive relative to the WRs around him unless the detail card clearly says: high current first-down/VORP edge, capped trust, short-window RB horizon risk, receiving-role durability review.

Recommended action: do not production-patch immediately; design a narrow RB v2 shadow test that only discounts short-window RBs when role durability/evidence is thin and WR opportunity cost is material.

## Josh Jacobs Deep Read

### What the model is seeing

- Active rank/score: `#32 / 41.2427`.
- Age: `28.2`.
- Role: `rb_short_window_three_down_role_asset`.
- Fragility: `rb_role_strong_but_age_sensitive`.
- Private VORP: `61.5`.
- Review scoring points: `197.1`.
- First-down points: `22.0`.
- Lifecycle modifier: `0.8944`.
- Confidence cap: `0.88`.
- Warnings: partial first-down confidence cap, RB age after 27 active, age-window caution active, route/role evidence missing.

### Is he high because of current production, role security, or lagging age penalty?

All three matter, but the active row already includes an age/lifecycle penalty. He is not top 15 or top 20. The score is supported by current role/VORP and first-down points, but the age-window warning is correctly active.

### Does his age/workload profile historically decay faster than the model accounts for?

The repo cannot prove this yet. The historical harness is rookie replay, not veteran RB age-season decay. The shadow RB horizon did move Jacobs from `#32` to `#41`, but that was part of a broad shadow policy that was not accepted for production.

### What would make the model right?

- He retains three-down/high-touch role.
- First-down scoring continues to reward his profile.
- The active age penalty is enough for a 28.2-year-old workhorse in this league.
- The surrounding WRs are also capped or source-limited.

### Jacobs verdict

`inconclusive / model probably about right to slightly high`

At #32 he is not an obvious model failure. The age/horizon warning should remain visible. A future RB v2 should test whether 28-plus workhorse scores need a modest retained-value cap, but the current evidence does not justify an emergency production change.

## WR Opportunity-Cost Comparison

James Cook is the real concern. He is above:

- Zay Flowers `#12`
- A.J. Brown `#13`
- Chris Olave `#14`
- Nico Collins `#16`
- Drake London `#19`
- CeeDee Lamb `#20`
- Justin Jefferson `#22`

Cook's current first-down/VORP signal is strong enough that the rank might be an intentional model edge. But in dynasty, the useful-window and replacement-fragility gap between a 26.6-year-old RB with receiving-role fragility and young/prime WR target earners is a valid concern.

Josh Jacobs sits near:

- Breece Hall `#31`
- Jaylen Waddle `#33`
- Michael Wilson `#34`
- Tee Higgins `#35`
- DK Metcalf `#36`
- Saquon Barkley `#38`

That rank band is more defensible. Jacobs is not burying cornerstone WRs; he is in a mixed review tier with age and partial-evidence warnings.

## Watch RB Verdicts

| Player | Verdict | Why |
|---|---|---|
| James Cook | Inconclusive / leaning too high | Real first-down/VORP and historical hit receipt, but #11 vs prime WRs may overweight short-window role. |
| Josh Jacobs | Inconclusive / about right to slightly high | Age penalty active; #32 is plausible but retained-value data is missing. |
| Bijan Robinson | Model probably right | Young elite multi-signal RB. |
| Jahmyr Gibbs | Model probably right | Young elite multi-signal RB; historical family is strong. |
| Jonathan Taylor | Model probably right but watch age | Extreme current evidence; age warning active. |
| De'Von Achane | Inconclusive / fragility watch | Difference-maker evidence and first-down value, but short-window/fragility should be explicit. |
| Kyren Williams | Model probably too high | Current role is valuable, but confidence cap and partial first-down warning argue for stronger horizon caution. |
| Chase Brown | Inconclusive / probably too high at top-24 | Historical hit receipt exists, but late-capital/current short-window profile is volatile. |
| Breece Hall | Model probably too low or data-limited | Strong original profile, younger age, but current private components are weaker/partial. |
| Saquon Barkley | Model probably right | Productive but age cliff already active. |
| Christian McCaffrey | Inconclusive / short-window edge | Massive evidence; age guardrail active; dynasty horizon still risky. |
| Derrick Henry | Model probably right | Extreme age cliff active and rank is no longer top tier. |
| Travis Etienne | Model probably too high / data issue | Age warning, source/team warning, no historical component. |
| Kenneth Walker | Inconclusive / data issue | Source/team warning and missing stats-first evidence. |
| Rachaad White | Model probably right | Role fragility and age caution keep him low. |
| Tony Pollard | Model probably right | Age/lifecycle penalties keep him out of core tier. |
| Chuba Hubbard | Model probably right | Role fragility and low VORP support low rank. |
| Jaylen Warren | Model probably too high | Age 27.5, no historical component, short-window rushing role; rank #43 may overstate horizon. |

## Model-Right Cases

The model may be right when:

- A young/prime RB has imported first-down evidence, high VORP, high review points, and no age penalty.
- The profile has early/middle draft capital plus receiving+rushing evidence in the historical rookie replay.
- The league's first-down scoring makes efficient, high-touch RBs harder to replace than generic dynasty intuition suggests.
- The score is accompanied by capped trust and visible short-window warnings.

Cook has enough evidence to be a possible model-right edge, but not enough to be treated as clean.

## Model-Wrong Cases

The model may be wrong when:

- Current-year RB VORP acts like a dynasty retained-value proxy.
- A short-window role label is allowed to outrank prime WR target earners without a durability gate.
- Missing route/target/snap evidence is shown only as a warning but not reflected enough in confidence.
- Late-capital or role-dependent backs get the same horizon treatment as elite young RBs.
- Age-27-plus backs with partial first-down evidence are not separated into floor/useful-window risk.

The highest-risk current rows are Cook, Kyren, Chase Brown, Etienne, and Warren. Jacobs is a watch item but not the most urgent.

## Recommended Shadow RB v2 Test

Do not promote the previous `rb_dynasty_horizon` experiment. It was too broad.

A better v2 shadow test should target only the issue supported by this audit:

### Hypothesis

The current model overvalues short-window RB production when role durability, receiving path, or multi-year retained-value evidence is thin, especially when the RB is being ranked above young/prime WRs.

### Candidate rule shape

- Preserve elite young multi-signal RBs.
- Preserve RBs with strong private first-down/VORP evidence but add explicit horizon/fragility reason codes.
- Apply only modest score pressure to short-window RBs when:
  - role is `rb_short_window_rushing_role_asset` or role fragility review,
  - age/lifecycle caution is active, or
  - confidence is capped due partial/missing evidence,
  - and the row sits in a WR opportunity-cost band.
- Do not touch RBs with already-low VORP/role-fragility scores unless the movement is purely explanatory.
- Do not use market, league, ADP, consensus, projections, prior draft, or legacy scores.

### Expected effects

- James Cook: small/moderate discount or stronger confidence warning; not a hard collapse.
- Josh Jacobs: modest age/horizon discount only if retained-value gate fails.
- Bijan/Gibbs/Taylor: mostly preserved.
- Achane/Kyren/Brown: move enough to expose fragility if the evidence is too short-window.
- CMC/Henry/Saquon: no emergency patch; age guardrails already active, but v2 can report window risk.

### Risks

- Suppressing real RB hits like Cook, Achane, Kyren, and Chase Brown.
- Overcorrecting into generic dynasty WR bias.
- Double-counting existing RB age curves.
- Penalizing first-down scoring impact even though this league rewards it.

## Bottom Line

James Cook at #11 is not obviously wrong from the private evidence, but it is aggressive. The model is seeing strong current VORP, strong first-down value, age still in range, and a historical hit receipt. The concern is that his active role label and warning flags say "short-window/rushing role/receiving fragility", which should not be invisible when he is above prime WRs.

Josh Jacobs at #32 is less alarming. The model already applies age and lifecycle caution. He should remain a review/watch row, not an emergency patch target.

Recommended next step: build a narrow shadow RB v2 focused on short-window RB horizon and WR opportunity cost, with upside/floor/fragility split in reason codes. Do not change active `latest` until that shadow test proves it improves historical RB metrics without suppressing real RB hits.
