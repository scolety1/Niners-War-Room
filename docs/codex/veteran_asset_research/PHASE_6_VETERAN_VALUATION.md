# Veteran Valuation Model for LVE Dynasty League

## Executive summary

For LVE, veteran valuation should be driven first by *current NFL role and current fantasy-scoring translation*, not by generic dynasty market prices. In a 10-team, 1QB, no-PPR, no-TE-premium league with 3 WR and 2 flex, the structural scarcity premium on quarterbacks and tight ends is lower than in the formats most public dynasty tools are built around, while startable RB/WR depth is more important. Public dynasty tools are often calibrated to Superflex, full-PPR, 12-team, and TE-premium environments, so they are useful only as capped market context, not as the core valuation engine for LVE. citeturn29view0turn29view4turn18search1

The strongest evidence-backed veteran inputs are role and usage. For pass-catchers, target share is one of the stickiest year-over-year statistics, and yards per route run is meaningfully stickier than many box-score measures. For quarterbacks, EPA per passing attempt and sack-avoidance metrics carry moderate year-over-year signal, but both still need team-context adjustment. For running backs, volume and high-value touches matter much more than rushing efficiency alone, and pure rushing efficiency is much noisier year over year than receiver usage stats. citeturn38view0turn36view0turn25view0turn40view0turn40view1

LVE’s no-PPR plus 0.4 points per rushing/receiving first down changes veteran valuation in a specific direction: empty catches lose importance, while roles that create first downs, goal-line work, yardage, and touchdowns gain importance. First-down data is useful, but projection error is real; first downs are harder to project than yards, so first-down rates should be used as a real-role modifier, not a primary standalone driver. citeturn12view0turn21search8turn22search4

Age and injury matter, but by position. Running backs decline earliest, wide receivers next, quarterbacks latest, and tight ends only look like they age especially well if you let a handful of generational outliers distort the sample. Rushing quarterbacks also age differently from pocket passers because rushing production tends to fall off earlier. Lower-body injuries matter most for RB/WR/TE, and Achilles injuries deserve special caution. citeturn39view0turn39view1turn39view2turn39view3turn6view3turn7view0

League rank is **not** player quality. In LVE it is a summer forced-release governance mechanism. It should affect only forced-release exposure, trade timing, and reacquisition strategy. It should **not** alter `veteran_base_value`, `horizon_retention_score`, or `keeper_score`.

## Position-specific valuation frameworks

### Quarterback

**Evidence-backed core:** current starting security, passing touchdown/yardage environment, rushing contribution, passing efficiency, and sack avoidance. In weekly fantasy scoring, passing touchdowns and passing yards dominate quarterback scoring, while rushing remains a real ceiling/floor amplifier. Separately, EPA per passing attempt and sack-avoidance metrics carry moderate year-to-year predictive value, but both need context adjustment because passing efficiency is partly owned by the team environment. citeturn25view0turn38view0

**LVE overlay:** suppress quarterbacks structurally after the football score is computed. In public Superflex markets, quarterbacks flood the top of overall rankings; in non-Superflex overall dynasty rankings, WRs and RBs dominate the top tier. LVE is even more anti-QB than generic 1QB dynasty because it is 10-team, not 12-team, and because the draft pool also includes released veterans and free agents. So even strong veteran QBs should usually lose overall keeper and trade priority to similarly strong RBs and WRs unless they are elite difference-makers. citeturn18search1turn29view4turn29view0

**Injury nuance:** do not hard-penalize a QB merely for being mobile. Evidence cited in quarterback rushing-injury analysis suggests designed QB runs are not automatically the most dangerous plays; actual missed time, current medical status, and whether the player takes avoidable sacks or reckless hits matter more. citeturn32search12turn32search0

### Running back

**Evidence-backed core:** touch share, high-value touches, goal-line role, receiving role, and overall usage dominate veteran RB valuation. Expected-fantasy-point work consistently treats opportunity as the baseline and efficiency as the regression-prone overlay; the same work also shows that target value and red-zone usage materially alter RB fantasy value. Sharp’s scoring review likewise shows RB1 spike weeks are typically built on heavy touches and touchdowns. citeturn36view0turn27view0

**Efficiency handling:** rushing efficiency is useful, but mostly as a secondary or tie-breaking layer. PFF’s RB work argues that yards after contact and missed tackles forced are the most player-owned rushing-efficiency stats, yet broader year-over-year work shows rushing stats still have weak stickiness compared with receiver usage stats. That means RB creation metrics should elevate or downgrade within a role tier, but should not overpower actual workload. citeturn40view0turn40view1turn38view0

**LVE overlay:** no-PPR reduces the value of “catch-only” receiving roles, but the first-down bonus pulls some value back to backs who are actually used to move chains. Goal-line, short-yardage, early-down workload, and red-zone access matter more in LVE than in generic PPR dynasty. Satellite backs remain useful, but they belong below true three-down or chain-moving roles unless their receiving workload is truly elite. citeturn12view0turn36view0

### Wide receiver

**Evidence-backed core:** target earning, route participation, per-route efficiency, and role robustness are the heart of veteran WR valuation. Target share is one of the stickiest WR/TE metrics year over year, yards per route run carries strong signal, and “getting open” is itself a measurable, stable trait. Route participation matters because a snap spent blocking or rotating off the field is not a target opportunity. citeturn38view0turn23view0turn9view0

**LVE overlay:** 3 WR plus 2 flex makes usable WR depth more valuable than in smaller-start leagues. That means the model should give real keeper value to reliable WR2/WR3 archetypes, not just alpha target hogs. At the same time, no-PPR means raw receptions are a trap. A low-aDOT receiver living on short catches must be graded through yardage, first downs, touchdown role, and route-based target earning, not catch totals alone. Public depth-heavy WR valuations translate better to LVE than public QB or TE valuations, but they still need scoring translation. citeturn29view0turn12view0turn21search8turn22search4

### Tight end

**Evidence-backed core:** route participation, target earning, yards per route run, and inverse blocking suppression drive veteran TE value. Route participation is the key filter because blocking-heavy tight ends can have acceptable snap shares while still offering weak fantasy opportunity. Quantitative TE work also suggests YPRR is fairly stable for the position, while blocking/route suppression is a real fantasy drag. citeturn9view0turn9view2turn24search1turn13search6

**LVE overlay:** apply structural suppression to TE after calculating football/fantasy strength. No TE premium and only one TE starter mean a non-elite TE should usually lose value to similarly strong WR/RB options. The elite TE tier still matters, but the bar should be high: the player needs strong routes, strong target earning, and strong receiving efficiency. Typical tight ends also age less gracefully than the position’s famous outliers make it seem. citeturn24search7turn26search5turn39view3

## Full feature audit tables

These weight ranges are **model-design ranges for LVE**, not empirically estimated coefficients. All feature inputs should be normalized to 0-100 before weighting.

### Quarterback feature audit

| position | feature_name | feature_category | definition | expected_direction | evidence_strength | predictive_target | LVE importance | recommended_weight_min | recommended_weight_max | missing_data_penalty | confidence impact | risk_flag | upside_flag | floor_flag | failure_modes | source_summary | citation_links | implementation_notes |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|
| QB | start_security | role | Likelihood of holding the starting job for most of the season | Higher is better | High | fantasy scoring, keeper, trade | Very high | 22 | 30 | High: impute neutral 50, -12 confidence | Very high | Low score = major risk | High score + long leash | High score supports floor | Good QB2s can still be replaceable in 1QB | Weekly QB scoring only matters if the player starts; LVE replacement level is high at QB | citeturn25view0turn29view0 | Core input; use depth-chart tier, coaching statements, and contract context |
| QB | passing_td_yardage_output | production | Passing TD and passing-yard ceiling/floor translated to LVE scoring | Higher is better | High | fantasy scoring | High | 16 | 24 | Medium: -6 confidence | High | Low if offense weak | High in strong offenses | High if stable volume | 3-point pass TD reduces dominance vs standard 4-point settings | Passing TDs and yards drive QB weekly scoring more than most rate stats | citeturn25view0 | Normalize using projected passing TDs/yards with LVE scoring applied |
| QB | rushing_value | role/production | Designed rush + scramble production, especially goal-line rushing | Higher is better | High | fantasy scoring, weekly ceiling | Medium-high | 12 | 18 | Medium: -6 confidence | High | Low rushing reduces ceiling | High rushing = spike weeks | Moderate if stable usage | 1QB still suppresses market value even for good rushers | Rushing boosts QB fantasy scoring, but should not override 1QB scarcity realities | citeturn25view0turn39view2 | Core for raw points; apply structural 1QB suppression later |
| QB | passing_efficiency_epa | efficiency | EPA/pass attempt or similar passing efficiency metric | Higher is better | Medium | real NFL success, fantasy support | Medium | 8 | 14 | Medium: -5 confidence | Medium | Low score flags shaky offense | High score lifts ceiling | Moderate | Team/scheme dependence can misassign credit | EPA/pass attempt is moderately sticky but partly a team stat | citeturn38view0 | Secondary input; downweight after team change |
| QB | sack_avoidance | negative_play_control | Sack rate or pressure-to-sack control | Lower sacks is better | Medium | fantasy support, job stability | Medium | 6 | 10 | Medium: -5 confidence | Medium | High sack rate = risk | Low sack rate boosts efficiency confidence | Supports floor | OL and scheme can muddy attribution | Sack-avoidance metrics have moderate signal and sacks are materially harmful | citeturn38view0 | Secondary input; use inverse normalization |
| QB | age_curve_archetype | aging | Pocket vs rushing-QB age translation | Younger/prime is better | Medium | keeper, horizon | Medium | 6 | 10 | Low: -3 confidence | Medium | Rushing QB 29+ = risk | Pocket QB 30-33 can still hold value | Mature pocket QB can be stable | One-size age penalty misprices archetypes | Pocket passers age later than dual-threat QBs; rushing falls earlier | citeturn39view2turn10search1 | Split QB age curve into pocket and rushing archetypes |
| QB | current_injury_durability | health | Current injury status plus recent availability | Healthier is better | High | fantasy scoring, keeper | High | 6 | 10 | High: -10 confidence | Very high | Active injury = major risk | Clean bill boosts trust | Healthy durable starters have floor | Over-penalizing old, resolved injuries | Use actual missed time/current status more than style stereotypes | citeturn6view3turn7view0turn32search12 | Direct penalty for active constraints; historical issues mostly risk/confidence |
| QB | environment_support | context | OL, pass catchers, coordinator/play volume/red-zone quality | Better is better | Medium | fantasy scoring | Medium | 4 | 8 | Low: -3 confidence | Medium | Bad environment increases fragility | Strong environment unlocks ceiling | Supports floor | Team changes can swing quickly | QB efficiency is partly team-owned; supporting cast matters | citeturn38view0turn25view0 | Use as overlay, not core talent score |
| QB | team_commitment_contract | security | Organizational commitment, guarantees, and replacement risk | Stronger commitment is better | Low-medium | keeper, trade | Medium | 0 | 4 | Low: -3 confidence | Medium | Weak commitment = bench risk | Strong commitment stabilizes value | Moderate | Teams can still pivot quickly | Helpful for role certainty, not direct scoring | citeturn29view0 | Confidence modifier more than scoring driver |
| QB | stale_nfl_draft_capital | rejected/display_only | Original NFL draft slot after multiple pro seasons | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | Can mislead | None | None | Double-counts status already expressed through current role | Current role and performance dominate historical entry point for veterans | citeturn38view0turn25view0 | Show in profile only; use only for extremely thin-sample passers |

### Running back feature audit

| position | feature_name | feature_category | definition | expected_direction | evidence_strength | predictive_target | LVE importance | recommended_weight_min | recommended_weight_max | missing_data_penalty | confidence impact | risk_flag | upside_flag | floor_flag | failure_modes | source_summary | citation_links | implementation_notes |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|
| RB | touch_share | role | Share of team RB rushes + targets/opportunities | Higher is better | High | fantasy scoring, keeper | Very high | 18 | 24 | High: -10 confidence | Very high | Low share = committee risk | Large share = upside | Large share supports floor | Empty touches can still underperform | xFP work and weekly scoring studies both point first to volume | citeturn36view0turn27view0 | Core input; prefer team-adjusted opportunity share |
| RB | high_value_touches | role | Red-zone work, inside-10 volume, and target quality | Higher is better | High | fantasy scoring | Very high | 14 | 20 | Medium: -6 confidence | High | Lack of high-value work caps ceiling | Strong red-zone + target role = upside | Strong if role stable | TD variance can still bite | Opportunity quality matters, not just quantity | citeturn36view0 | Core input; combine red-zone carries and target value |
| RB | goal_line_short_yardage_role | role | Role on inside-5 carries and short-yardage plays | Higher is better | High | fantasy scoring, first-down scoring | High | 10 | 16 | Medium: -5 confidence | High | Losing this role is a red flag | Strong positive in LVE | Strong for week-to-week floor | Could be vultured by QB/teammate | LVE boosts TDs and rushing first downs, so chain-moving power matters | citeturn12view0turn27view0 | Core LVE overlay |
| RB | receiving_role_no_ppr_adjusted | role | Routes, targets, two-minute role, receiving share, but discounted for no-PPR | Higher is better | High | fantasy scoring, keeper | High | 8 | 14 | Medium: -5 confidence | High | Satellite-only backs can be fragile in LVE | Strong receiving on top of rushing is huge | Moderate alone, strong in combo | Pure checkdown role can disappoint without TDs/FDs | Targets matter for RBs, but no-PPR reduces pure reception payoff | citeturn36view0turn12view0 | Count role, not raw catches |
| RB | rush_efficiency_creation | efficiency | YAC/att, missed tackles forced, elusive rating, similar self-created rushing measures | Higher is better | Medium | real NFL success, tie-break fantasy | Medium | 8 | 12 | Medium: -4 confidence | Medium | Weak creation lowers contingency upside | Strong creation can win more work | Helps floor if role exists | Role can swamp efficiency | RB creation metrics isolate player skill better than YPC, but rushing stats are noisy | citeturn40view0turn40view1turn38view0 | Secondary input; never above workload |
| RB | first_down_conversion_profile | chain_moving | Rush/rec first-down generation or short-yardage conversion profile | Higher is better | Medium | fantasy scoring, floor | Medium-high | 6 | 10 | Medium: -4 confidence | Medium | Poor chain-movers can lose snaps | Strong chain-movers fit LVE | Supports floor | First downs are harder to project than yards | First-down scoring helps backs who move chains, but projection noise is real | citeturn12view0 | Secondary overlay; use actual first-down rates when available |
| RB | offense_environment_line | context | Team scoring, OL quality, run environment | Better is better | Medium | fantasy scoring | Medium | 4 | 8 | Low: -3 confidence | Medium | Weak offense caps TDs | Strong offense boosts upside | Supports floor | Team changes swing fast | RB results remain environment-sensitive | citeturn38view0turn40view2 | Overlay only |
| RB | age_curve | aging | Position-specific age decline | Younger/prime is better | High | keeper, horizon | High | 8 | 12 | Low: -3 confidence | Medium | RB 27-28+ rises sharply in risk | Very young lead backs have premium | Prime-age workhorses have floor | Older outliers exist, but not often | RB peak happens earliest among fantasy skill positions | citeturn39view0turn10search2turn10search6 | Use strong penalties from late-20s onward |
| RB | injury_durability | health | Current injury, recent missed games, lower-body severity | Healthier is better | High | fantasy scoring, keeper | High | 6 | 10 | High: -10 confidence | Very high | Lower-body recurrence = risk | Healthy RBs gain trust | Durable backs have floor | Old resolved injury can be overcounted | RB is highly sensitive to lower-body injuries and missed time | citeturn6view3turn7view0turn32news30 | Active injury affects score; history mostly risk/confidence |
| RB | contingent_upside | upside_only | Backup/committee back’s path to lead role if depth chart changes | Higher is better | Low-medium | dynasty stash value | Medium | 0 | 6 | Low: -2 confidence | Medium | If no path, stash risk rises | Strong path = upside stash | Weak floor | Can become pure handcuff chasing | Useful in deep benches, but contingent value is speculative | citeturn29view0 | Upside flag, not a core base-value driver |
| RB | raw_receptions | rejected/display_only | Pure catch total without role/yardage/FD context | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | Can overrate satellites | None | None | Misprices no-PPR leagues | No-PPR and first-down scoring require role translation, not catch totals | citeturn12view0turn36view0 | Display-only; fold into receiving role instead |
| RB | career_touches_mileage | rejected/display_only | Lifetime touch count as a direct score input | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | Can double-count age/injury | None | None | Confuses age, health, and current role | Better captured through age, injury, and current role erosion | citeturn39view0turn6view3 | Use only as note, not score |

### Wide receiver feature audit

| position | feature_name | feature_category | definition | expected_direction | evidence_strength | predictive_target | LVE importance | recommended_weight_min | recommended_weight_max | missing_data_penalty | confidence impact | risk_flag | upside_flag | floor_flag | failure_modes | source_summary | citation_links | implementation_notes |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|
| WR | route_participation | role | Share of pass plays on which the WR actually runs a route | Higher is better | High | fantasy scoring, keeper | Very high | 12 | 18 | High: -8 confidence | High | Low routes = role fragility | Full-time routes unlock ceiling | Full-time routes support floor | Some vertical specialists still score on lower routes | Players cannot earn targets when not on routes | citeturn9view0 | Core input; preferable to raw snap share |
| WR | target_share | usage | Share of team targets while active | Higher is better | High | fantasy scoring, keeper, trade | Very high | 14 | 20 | Medium: -5 confidence | High | Low share = replaceable role | High share = alpha upside | High share supports weekly floor | Bad QB play can depress box scores | Target share is one of the stickiest pass-catcher metrics | citeturn38view0turn13search0 | Core input |
| WR | targets_per_route_run | usage/earning | Target rate conditional on route participation | Higher is better | High | fantasy scoring, talent translation | High | 10 | 16 | Medium: -5 confidence | High | Weak earning on full routes = warning | Strong earning = major upside | Strong with stable routes | Small samples can mislead | Per-route target earning is central to WR opportunity quality | citeturn22search12turn13search0 | Core if enough routes; else confidence penalty |
| WR | yards_per_route_run | efficiency | Receiving yards per route run | Higher is better | High | fantasy scoring, keeper | High | 10 | 16 | Medium: -4 confidence | Medium-high | Low YPRR on big routes = concern | High YPRR = spike upside | Strong if paired with routes/targets | Can be inflated by small role or big-play specialists | YPRR is one of the better public efficiency metrics for pass catchers | citeturn23view0turn38view0turn22search0 | Core secondary; pair with route size |
| WR | first_downs_per_route | chain_moving | First downs generated per route or equivalent chain-moving profile | Higher is better | Medium | fantasy scoring, floor | Medium-high | 6 | 10 | Medium: -4 confidence | Medium | Low FD rate in no-PPR lowers value | Strong chain movers fit LVE | Supports floor | Direct FD projection is noisy | First-downs-per-route is used as a predictive stat, but standalone projection is still imperfect | citeturn21search8turn22search4turn12view0 | Secondary LVE overlay |
| WR | get_open_role_robustness | film/trait | Ability to earn separation and keep role across coverages/alignments | Higher is better | Medium | keeper, role stability | Medium | 8 | 12 | Medium: -4 confidence | Medium | One-dimensional role = fragility | Robust route winners have upside | Two-way role supports floor | Film/charting availability may be limited | “Getting open” shows strong year-to-year signal, especially versus man | citeturn23view0 | Secondary input or confidence booster if charting exists |
| WR | td_area_air_yards_role | usage | End-zone usage, air-yard depth, TD-area role | Higher is better | Medium | fantasy scoring, ceiling | Medium | 6 | 10 | Medium: -4 confidence | Medium | Low-value short-only role caps upside | Deep + end-zone role boosts ceiling | Not enough for floor alone | TD variance remains high | Deeper, high-value targets matter more than raw catches | citeturn37search0turn25view0 | Upside/ceiling input |
| WR | offense_environment | context | Team pass volume, QB quality, scoring environment | Better is better | Medium | fantasy scoring | Medium | 4 | 8 | Low: -3 confidence | Medium | Bad offense lowers floor | Elite offenses create upside | Helps floor | Team change volatility | WR output still reflects team environment and QB quality | citeturn38view0turn37search0 | Overlay only |
| WR | age_curve | aging | Position-specific aging translation | Younger/prime is better | High | keeper, horizon | High | 8 | 12 | Low: -3 confidence | Medium | 30+ raises decline risk | Young established earners have upside | Prime-age earners have floor | Some elites age gracefully | WRs peak later than RBs but still earlier than old-market optimism suggests | citeturn39view1 | Moderate age penalty after prime |
| WR | injury_durability | health | Current health, games missed, lower-body severity | Healthier is better | High | keeper, trade, scoring | High | 4 | 8 | High: -8 confidence | High | Recurring lower-body issues = risk | Clean health boosts trust | Healthy route earners keep floor | Overcounting fully resolved issues | Lower-body injuries matter for explosive movement and route volume | citeturn6view3turn7view0 | Active issues hit score; history mostly confidence/risk |
| WR | return_role | league_specific_overlay | Kick/punt return usage with real chance to persist | Higher is better | Low | fantasy scoring fringe value | Low-medium | 0 | 4 | Low: -2 confidence | Low | Specialist-only trap | Plus return role can matter in LVE | Low floor by itself | Role can vanish quickly | LVE rewards return yards, but this is volatile and role-dependent | citeturn12view0 | Upside flag only; never core |
| WR | raw_receptions | rejected/display_only | Catch totals without route, yardage, FD, or depth context | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | Overrates low-aDOT catch traps | None | None | Misprices no-PPR roles | Empty catches are less useful in LVE than in PPR | citeturn12view0turn37search0 | Display-only; translate through route/target/FD profile |

### Tight end feature audit

| position | feature_name | feature_category | definition | expected_direction | evidence_strength | predictive_target | LVE importance | recommended_weight_min | recommended_weight_max | missing_data_penalty | confidence impact | risk_flag | upside_flag | floor_flag | failure_modes | source_summary | citation_links | implementation_notes |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|
| TE | route_participation | role | Share of team pass plays on which TE runs a route | Higher is better | High | fantasy scoring, keeper | Very high | 18 | 24 | High: -10 confidence | Very high | Low routes = replaceable TE | Elite routes = rare upside | High routes support floor | Some part-time TEs can TD-binge | Routes matter more than snaps for fantasy TEs | citeturn9view0turn9view2 | Core TE input |
| TE | target_earning | usage | Target share and/or targets per route run | Higher is better | High | fantasy scoring, keeper | Very high | 16 | 22 | Medium: -5 confidence | High | Low earning with big routes is bad | Strong earning is how TEs clear suppression | Strong only if routes are real | Small-sample spikes mislead | TE scoring requires real receiving role, not empty snaps | citeturn13search6turn24search1 | Core input; combine share and per-route if possible |
| TE | yards_per_route_run | efficiency | Receiving yards per route run for TEs | Higher is better | Medium-high | fantasy scoring, keeper | High | 12 | 18 | Medium: -4 confidence | Medium | Low YPRR can expose fragile role | High YPRR identifies difference-makers | Paired with routes/targets improves floor | Can be inflated by small role | YPRR is relatively stable for TEs and useful for separating true receiving TEs | citeturn24search1turn13search6 | Core secondary |
| TE | blocking_suppression_inverse | role | Penalty for inline/blocking-heavy deployment that cuts routes | Higher is better | High | fantasy scoring | High | 10 | 16 | Medium: -5 confidence | High | Blocking-heavy TEs are traps | Route-unlocked TEs gain upside | Strong if paired with route volume | Some strong blockers still matter if routes stay high | Blocking usage is a direct fantasy opportunity suppressor | citeturn9view0turn9view2 | Use inverse of blocking-heavy deployment |
| TE | td_area_adot_role | usage | End-zone role and usable target depth | Higher is better | Medium | fantasy scoring, ceiling | Medium | 6 | 10 | Medium: -4 confidence | Medium | Flat role caps upside | End-zone + downfield TE has breakout chance | Weak without route volume | TDs volatile, aDOT alone noisy | TE ceiling is often tied to rare high-value targets | citeturn24search1turn9view2 | Upside input only |
| TE | first_down_profile | chain_moving | Receiving first-down contribution or first-downs per route | Higher is better | Medium | fantasy scoring, floor | Medium | 4 | 8 | Medium: -3 confidence | Medium | Low FD role hurts in LVE | Strong chain-moving boosts non-premium value | Helps floor | Direct projection noisy | First-down scoring helps TEs, but only if they are real movers of chains | citeturn12view0turn22search4 | Secondary overlay |
| TE | age_curve | aging | Position-specific age translation with outlier control | Younger/prime is better | Medium-high | keeper, horizon | Medium-high | 8 | 12 | Low: -3 confidence | Medium | Non-elite 30+ TE risk rises | Young elite TE gets premium | Prime-age elites have floor | Kelce/Gonzalez-style survivorship bias | Typical TE aging looks closer to WR once outliers are removed | citeturn39view3 | Do not assume TE ages “gracefully” unless truly elite |
| TE | injury_durability | health | Current health and lower-body availability | Healthier is better | High | keeper, score | Medium-high | 4 | 8 | High: -8 confidence | High | Missed time and lower-body issues raise risk | Healthy role-locked TE gains trust | Supports floor if role is real | Past injuries can be overcounted | Availability matters because TE elite window is often short | citeturn6view3turn39view3 | Active status matters more than old injury lore |
| TE | offense_environment | context | Team pass environment and QB quality | Better is better | Medium | fantasy scoring | Medium | 4 | 8 | Low: -2 confidence | Medium | Weak offense lowers target quality | Good offense unlocks ceiling | Moderate floor support | Team change volatility | TE fantasy output still depends on pass volume and QB competence | citeturn38view0turn13search6 | Overlay only |
| TE | athletic_profile | secondary_trait | Athletic traits that may support rare ceiling if role already exists | Higher is better | Low-medium | upside | Low | 0 | 6 | Low: -2 confidence | Low | Can overrate workout TE | Rare ceiling if paired with routes | Weak alone | Athletic “empty calories” if role poor | Athleticism matters only after role/target filters clear | citeturn9view2turn39view3 | Secondary-only |
| TE | generic_te_scarcity | rejected/display_only | Broad TE scarcity premium from TE-premium discourse | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | Can wildly overprice TE in LVE | None | None | Imports wrong format incentives | No-TE-premium LVE should not inherit TE-premium economics | citeturn24search7turn29view0 | Display-only warning |
| TE | stale_nfl_draft_capital | rejected/display_only | Original draft slot after role is already known | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | Can bias toward dead-name veterans | None | None | Double-counts role and reputation | Current route/target role matters more for veterans | citeturn9view2turn38view0 | Only note for very early-career edge cases |

### Rejected and display-only global features

| position | feature_name | feature_category | definition | expected_direction | evidence_strength | predictive_target | LVE importance | recommended_weight_min | recommended_weight_max | missing_data_penalty | confidence impact | risk_flag | upside_flag | floor_flag | failure_modes | source_summary | citation_links | implementation_notes |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|
| ALL | generic_adp | rejected/display_only | One-number public market price without LVE translation | Do not score directly | Low | trade context only | Display only | 0 | 0 | None | Low | Misprices format | None | None | Public tools are mostly built for non-LVE settings | Most dynasty markets are Superflex/PPR/12-team/TE-premium oriented | citeturn29view0turn18search1turn29view4 | Use only as capped market overlay |
| ALL | broad_market_superflex_ppr_value | rejected/display_only | Consensus market value from formats unlike LVE | Do not score directly | Low | trade context only | Display only | 0 | 0 | None | Low | Overvalues QBs/TEs, PPR traps | None | None | Imports wrong positional economics | Public dynasty defaults differ materially from LVE | citeturn29view0turn17search6turn17search21 | Cap and re-center if used at all |
| ALL | league_rank_as_talent | rejected/display_only | Treating league rank as a player-quality input | Do not score directly | None | none | None | 0 | 0 | None | None | Distorts player value | None | None | It is owner-opinion/governance, not NFL performance | League rank is only relevant to forced-release exposure in LVE |  | Never enter player-quality formulas |
| ALL | raw_touchdowns_only | rejected/display_only | Using prior TD totals without role context | Do not score directly | Low | none directly | Display only | 0 | 0 | None | Low | TD regression trap | None | None | Highly volatile | TDs matter, but are too noisy without role/usage context | citeturn25view0turn36view0 | Use in role context only |
| ALL | highlight_plays_social_buzz | rejected/display_only | Narrative/hype without role evidence | Do not score directly | None | none | None | 0 | 0 | None | None | Can cause reach errors | None | None | Pure noise | Not evidence-backed for a deterministic local model |  | Keep in manual notes only |

## Formulas and scoring rules

All exact coefficients below are **model-design choices for LVE**, not sourced coefficients.

### Veteran base value

`veteran_base_value` should measure how strong the player is **as an NFL fantasy contributor right now**, before LVE structural suppression is applied.

**QB**

`veteran_base_value_qb =`
- `0.28 * start_security`
- `+ 0.20 * passing_td_yardage_output`
- `+ 0.15 * rushing_value`
- `+ 0.12 * passing_efficiency_epa`
- `+ 0.10 * sack_avoidance`
- `+ 0.08 * age_curve_archetype`
- `+ 0.07 * current_injury_durability`

Why this shape: passing TDs/yards drive the most QB scoring, but rushing is still meaningful; start security is indispensable; efficiency and sack management matter, but not as much as actual scoring/playing-time inputs. citeturn25view0turn38view0

**RB**

`veteran_base_value_rb =`
- `0.22 * touch_share`
- `+ 0.18 * high_value_touches`
- `+ 0.14 * goal_line_short_yardage_role`
- `+ 0.12 * receiving_role_no_ppr_adjusted`
- `+ 0.10 * rush_efficiency_creation`
- `+ 0.08 * first_down_conversion_profile`
- `+ 0.06 * offense_environment_line`
- `+ 0.10 * age_curve`
- `+ 0.10 * injury_durability`

Why this shape: RB valuation starts with role, especially high-value role. Efficiency matters, but follows role rather than leads it. citeturn36view0turn27view0turn38view0

**WR**

`veteran_base_value_wr =`
- `0.16 * target_share`
- `+ 0.14 * route_participation`
- `+ 0.14 * targets_per_route_run`
- `+ 0.13 * yards_per_route_run`
- `+ 0.08 * first_downs_per_route`
- `+ 0.10 * get_open_role_robustness`
- `+ 0.07 * td_area_air_yards_role`
- `+ 0.06 * offense_environment`
- `+ 0.07 * age_curve`
- `+ 0.05 * injury_durability`

Why this shape: LVE WR valuation should start with earning targets and staying on routes, then add per-route efficiency and chain-moving ability. citeturn38view0turn23view0turn9view0

**TE**

`veteran_base_value_te =`
- `0.20 * route_participation`
- `+ 0.18 * target_earning`
- `+ 0.16 * yards_per_route_run`
- `+ 0.12 * blocking_suppression_inverse`
- `+ 0.08 * td_area_adot_role`
- `+ 0.06 * first_down_profile`
- `+ 0.08 * age_curve`
- `+ 0.06 * injury_durability`
- `+ 0.06 * offense_environment`

Why this shape: route access and target earning dominate TE value. Blocking-heavy TEs are often fantasy traps. citeturn9view0turn9view2turn24search1

### Horizon retention score

`horizon_retention_score` should estimate how likely the player is to keep useful value over the next 2-3 years.

**Generic structure**

`horizon_retention_score =`
- `0.35 * age_curve_score`
- `+ 0.25 * role_security_score`
- `+ 0.20 * injury_durability_score`
- `+ 0.10 * skill_portability_score`
- `+ 0.10 * team_commitment_score`

**Position-specific interpretation**
- For QB, `skill_portability_score` means passing profile + sack control.
- For RB, it means receiving portability and whether the role survives loss of ideal environment.
- For WR, it means target earning + role robustness.
- For TE, it means real receiving role rather than scheme-only gadget usage.

### Keeper score

`keeper_score = clamp(0.62 * veteran_base_value + 0.23 * horizon_retention_score + 0.10 * confidence_score + 0.05 * lve_format_fit - structural_penalty, 0, 100)`

Where:
- `lve_format_fit` rewards players whose scoring profile matches no-PPR + first-down + lineup depth.
- `structural_penalty` is **model-design**:
  - QB: `8 to 18` unless truly elite
  - TE: `6 to 14` unless truly elite
  - RB/WR: `0`

**Elite-release conditions**
- QB structural penalty can be cut in half only if:
  - `start_security >= 85`
  - `passing_td_yardage_output >= 80`
  - and either `rushing_value >= 75` **or** `passing_efficiency_epa >= 80`
- TE structural penalty can be cut in half only if:
  - `route_participation >= 85`
  - `target_earning >= 80`
  - `yards_per_route_run >= 75`

This is the cleanest way to be strict about not overvaluing QB in 1QB or TE in no-premium while still allowing truly exceptional players to clear the gate. The logic is league-specific model design, but it is directionally aligned with the way public values swing between 1QB and Superflex formats and the way TE-premium changes TE economics. citeturn29view0turn18search1turn24search7

### Drop candidate score

`drop_candidate_score = clamp(0.45 * (100 - keeper_score) + 0.25 * replaceability_score + 0.15 * injury_uncertainty_score + 0.15 * roster_clog_score, 0, 100)`

Where:
- `replaceability_score` is highest for QB2/QB3 and TE2/TE3 in LVE.
- `roster_clog_score` is high for players whose only value is contingent or name-based.
- `injury_uncertainty_score` rises for active recovery or unstable availability.

Interpretation:
- `0-24`: strong keep
- `25-49`: keep unless roster squeeze
- `50-69`: legitimate release candidate
- `70+`: strong drop or shop candidate

### Trade value

`trade_value = clamp(0.55 * keeper_score + 0.20 * market_proxy_capped + 0.15 * liquidity_score + 0.10 * confidence_score, 0, 100)`

Where:
- `market_proxy_capped` is a translated public-market score, never allowed to move more than:
  - `±8` points for QB and TE
  - `±12` points for RB and WR
- `liquidity_score` reflects how easy the asset is to move in the league economy.
- If the only market source is obviously non-LVE-formatted, compress it toward 50 before applying the cap.

This preserves market awareness without letting PPR/Superflex/TE-premium assumptions hijack LVE values. citeturn29view0turn17search5turn17search6

### Confidence score

`confidence_score = clamp(0.30 * data_completeness + 0.20 * role_certainty + 0.20 * injury_certainty + 0.15 * source_quality + 0.15 * signal_agreement, 0, 100)`

Use:
- `90+`: very high confidence
- `75-89`: high confidence
- `60-74`: medium confidence
- `<60`: review before money decisions

## Age, role, injury, scoring translation, and league-rank handling

### Age-curve rules

| archetype | evidence-backed direction | LVE model rule | citation |
|---|---|---|---|
| QB pocket passer | Ages later than dual-threat QBs; peak can extend into early 30s | Mild penalty through 30, moderate at 31-33, stronger at 34+ | citeturn39view2turn10search1 |
| QB rushing / dual-threat | Rushing production falls earlier; overall peak younger | Light penalty through 27-28, meaningful penalty from 29 onward | citeturn39view2 |
| RB | Earliest cliff of fantasy skill positions | Prime 22-25, moderate decline 26-27, strong penalty 28+ | citeturn39view0turn10search2 |
| WR | Later than RB, earlier than old-market optimism often assumes | Prime 24-29, moderate decline 30-31, stronger 32+ | citeturn39view1 |
| TE | Raw average is skewed by outliers; typical TE ages more like WR than like an immortal unicorn | Prime roughly mid-20s to late-20s; penalty starts around 30 unless truly elite | citeturn39view3 |

### Role and projection rules

| position | role rule | implementation direction | citation |
|---|---|---|---|
| QB | Prioritize *who starts*, then how they score | Locked starter > efficient bridge with rushing > pocket-only compiler > backup | citeturn25view0turn38view0 |
| RB | Prioritize workload and high-value touches over efficiency | Lead role + red-zone + chain-moving > pass-game-only satellite > pure backup | citeturn36view0turn27view0 |
| WR | Prioritize routes + target earning + per-route quality | Route-earning, target-earning WRs stay valuable in 3WR/2FLEX | citeturn38view0turn23view0turn9view0 |
| TE | Prioritize route access and receiving role | Receiving TE with real routes > blocking TE with decent snap rate | citeturn9view0turn9view2 |

### Injury and durability rules

| injury variable | score impact | confidence impact | position sensitivity | reasoning | citation |
|---|---|---|---|---|---|
| Active major injury / uncertain camp timeline | Strong direct penalty | Strong confidence penalty | All, especially RB/WR/TE | Current availability changes both projection and trust | citeturn6view3turn7view0 |
| Recent missed games without current issue | Small-moderate direct penalty | Moderate confidence penalty | All | Availability matters, but old injuries should not dominate | citeturn38view0turn6view3 |
| ACL history | Moderate penalty, strongest in first season back | Moderate confidence hit | RB/WR/TE > QB | Return is possible, but lower-body recovery matters | citeturn6view3 |
| Achilles history | Stronger penalty than ACL in most cases | Strong confidence hit | RB/WR/TE especially | Achilles return remains a material concern in NFL skill players | citeturn7view0 |
| Running-QB style alone | Usually confidence note only | Small | QB | Do not assume mobility alone equals higher injury rate; actual history matters more | citeturn32search12turn32search0 |

### League-rank handling

League rank should **not** move `veteran_base_value`, `horizon_retention_score`, or `keeper_score`. It is not an independent measure of player skill, fantasy fit, or NFL projection. It should create separate metadata only:
- `is_top5_league_ranked`
- `forced_release_exposure`
- `pre_declaration_trade_urgency`
- `reacquisition_priority_if_released`

### No-PPR and first-down scoring translation

| scoring element | translation rule | implication |
|---|---|---|
| Raw receptions | Do not score directly | Empty catches lose value |
| Targets/routes | Still core | Opportunity still creates yards, TDs, and first downs |
| First downs | Use as secondary role/floor modifier | Valuable in LVE, but noisy to project directly |
| TD-area work | Upweight | TDs remain heavily weighted |
| Goal-line role | Upweight, especially for RB | Huge in LVE |
| QB rushing vs passing | Keep for raw fantasy value, but suppress by 1QB scarcity later | Good rushing QB still not equal to elite WR/RB in overall LVE value |
| TE without premium | Require elite route/target profile to elevate | Most non-elite TEs remain structurally suppressed |

These scoring translations are supported directionally by first-down projection analysis and opportunity-value analysis, but the exact LVE coefficients are model design. citeturn12view0turn36view0turn37search8

## Implementation-ready CSV recommendations and test fixture recommendations

### CSV recommendations

| file | purpose | required columns | implementation notes |
|---|---|---|---|
| `veteran_player_inputs.csv` | Raw player/state inputs | `player_id`, `player_name`, `team`, `position`, `age`, `years_exp`, `starter_status`, `games_played_prev`, `games_missed_2yr`, `current_injury_status`, `depth_chart_tier`, `contract_years_left`, `guaranteed_money_flag`, `projected_role_note` | Manual-friendly master input file |
| `veteran_feature_registry.csv` | Feature metadata | `feature_name`, `position`, `feature_category`, `evidence_strength`, `use_type`, `default_weight`, `min_weight`, `max_weight`, `missing_data_penalty`, `description`, `source_note` | One row per feature; supports deterministic math and audits |
| `veteran_feature_scores.csv` | Normalized feature scoring | `player_id`, `season`, `feature_name`, `raw_value`, `normalized_value`, `source_id`, `source_date`, `missing_flag`, `confidence_note` | Table-first audit file |
| `veteran_market_inputs.csv` | Public market overlay only | `player_id`, `market_source`, `format_tag`, `ranking_type`, `market_rank`, `market_score_translated`, `date_collected` | Never let this file directly drive base values |
| `veteran_model_outputs.csv` | Final model outputs | `player_id`, `model_version`, `veteran_base_value`, `horizon_retention_score`, `keeper_score`, `drop_candidate_score`, `trade_value`, `confidence_score`, `risk_flags`, `upside_flags`, `floor_flags` | Generated output; can be rebuilt locally |
| `veteran_provenance_notes.csv` | Manual note trail | `note_id`, `player_id`, `field_name`, `old_value`, `new_value`, `reason`, `source_type`, `entered_by`, `entered_at` | Required for overrides and handwritten-league-history reconciliation |
| `source_catalog.csv` | Source provenance | `source_id`, `source_name`, `source_type`, `url_or_file`, `collected_date`, `reliability_tier`, `format_context`, `notes` | Essential for explainability |
| `league_release_context.csv` | Forced-release context only | `team_id`, `player_id`, `league_rank_slot`, `top5_flag`, `forced_release_exposure`, `release_probability_note` | Keep separate from player-quality scoring |

### Test fixture recommendations

| fixture | expected model behavior |
|---|---|
| Elite dual-threat QB in 1QB | High `veteran_base_value`; strong `keeper_score`; still below elite RB/WR tier after structural QB suppression |
| Replaceable veteran QB | Adequate raw score possible, but low `keeper_score`, high `drop_candidate_score` because 1QB replacement is easy |
| Prime workhorse RB | Top-tier `keeper_score`; strong `trade_value`; low `drop_candidate_score` |
| Aging fragile RB | Good raw role may remain, but `horizon_retention_score` and `confidence_score` should shrink materially |
| Elite target-earning WR | Near-top overall value in LVE because 3 WR + 2 flex rewards stable WR volume |
| Low-aDOT reception trap WR | Raw catches should not save the profile; lower LVE fit than generic PPR models would assign |
| Elite route-earning TE | Clears structural TE suppression only if routes, targets, and YPRR are all elite |
| Non-premium replaceable TE | Fine `veteran_base_value` possible, but poor overall `keeper_score` compared with RB/WR alternatives |
| Forced-release top-five veteran | League-rank flags should change exposure metadata only; player-quality scores must remain unchanged |
| High public market value but lower LVE private value | `trade_value` may stay decent via liquidity/market, while `keeper_score` remains lower because LVE format fit is weaker |

## Open questions and limitations

The highest-confidence parts of this model are the role/usage hierarchy, the age-curve direction by position, the pass-catcher route/target framework, the need to structurally suppress QB/TE in LVE, and the decision to cap public-market inputs. The weakest areas are exact first-down projection coefficients, exact contract-security weights, and any attempt to turn public market prices into one “correct” LVE number. Those should be treated as model-design choices and tested before money decisions. citeturn12view0turn29view0turn38view0