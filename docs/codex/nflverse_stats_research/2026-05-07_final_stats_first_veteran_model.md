# Final Stats-First Veteran Model for the LVE Dynasty League

## Evidence base and league implications

The public data stack is strong enough to build a deterministic, stats-first dynasty model without using market data inside private value. The key pieces are all available through the nflverse ecosystem and linked public sources: weekly player stats with rushing first downs, expected fantasy/opportunity data with expected rushing and receiving first downs, snap counts, depth charts, advanced stats, Next Gen Stats, contracts, and a public consensus rankings feed for market-only use. There are two important caveats: nflverse participation data has limited live usefulness after the source change, and nflverse injury data currently has a post-2024 gap, so injury and route-participation handling need explicit fallbacks. citeturn3search0turn8view0turn26view0turn26view2turn5view5turn5view6turn5view7turn27search0turn28search1turn7search10

For this league, you should **not** use the default fantasy-point totals in expected-points packages as the final scoring target. The public expected-points stack explicitly includes receiving fantasy points under PPR assumptions, while your league is no-PPR with a **0.4 rushing/receiving first-down bonus**. The correct approach is to rebuild LVE scoring from the component expected fields: expected passing yards/TDs/INTs, expected rushing yards/TDs/first downs, and expected receiving yards/TDs/first downs. That is the single most important implementation rule in the whole model. citeturn8view0turn5view3turn3search0

The evidence base for the feature hierarchy is also clear. For pass catchers, target-earning signals matter more than raw box-score noise: targets correlate strongly with fantasy output, and targets per route run is useful because it blends intent with playing time; Fantasy Life’s public work shows 18 wide receivers topping 200 standard-scoring points over the last five years with TPRRs ranging from 22.1% to 36.6%, averaging 27.9%. YPRR is also useful, but SumerSports explicitly notes that standard YPRR is partly descriptive and biased by personnel/down-distance context; they report year-to-year stability of 0.51 for YPRR and 0.67 for expected YPRR. For running backs, workload beats raw touch counts: PFF’s public weighted-opportunity work shows weighted opportunity outperformed raw touches and raw opportunities in correlation to fantasy points, and even in standard formats a target was worth more than a carry. For tight ends, route involvement matters materially: public TE route-rate work shows strong threshold effects for weekly TE1 utility, and Sharp Football’s public TE work notes that YPRR is more stable for TEs than WRs while TE target-rate-per-route is materially weaker than the WR version. For quarterbacks, replacement level is high in 1QB formats, which is why elite separation matters but ordinary starter quality does not. citeturn29view4turn29view3turn30search2turn31search2turn31search12turn19search4turn19search13turn18search2

The age curve evidence supports separate treatment by position. Public age-curve work shows RB peaks earlier than WR, WR peaks earlier than pocket QBs, and TE ages are sensitive to elite-outlier distortion. Apex’s recent public studies put average peak ages at roughly 25.5 for RB, 26.9 for WR, 28.5 overall for QB, and 27.4 for TE, while also showing that dual-threat QBs peak earlier than pocket passers and that RB late-age seasons are far rarer than WR late-age seasons. ESPN’s public age-decline summary also flags a meaningful age-28/29 decline for RBs. That is why age belongs lightly in **private value**, but heavily in **dynasty hold** and **RB fragility**. citeturn15search0turn15search1turn15search3turn15search11turn13search6

For your exact format, the structural adjustments are straightforward. A 10-team 1QB league makes ordinary QBs replaceable. No TE premium and only one mandatory TE slot suppresses non-elite tight ends. But **3 WR plus 2 flex** materially boosts WR demand and keeps strong WR3/4 depth relevant even in no-PPR. The 0.4 first-down bonus also favors chain-movers over empty-volume players and makes first-down conversion rates a real scoring input rather than a tiebreaker. **Evidence-backed finding:** this setup should push the model toward WR target-earning and first-down creation, keep RB win-now value strong but fragile, and sharply separate elite from non-elite QB/TE profiles. **Model-design choice:** the formulas below implement that structure explicitly. citeturn18search2turn19search13turn29view4turn17search4

## Normalization and bucket construction

**Model-design choice**

Every raw input becomes a 0–100 score before entering any output formula.

### Core scoring rebuild

Let league constants be configuration parameters, not hard-coded assumptions:

- `pass_yd_pts`
- `pass_td_pts`
- `int_pts`
- `rush_yd_pts`
- `rush_td_pts`
- `rec_yd_pts`
- `rec_td_pts`
- `fumble_lost_pts`
- `fd_bonus = 0.4`

Then define:

`actual_lve_points = passing_yards*pass_yd_pts + passing_tds*pass_td_pts + interceptions*int_pts + rushing_yards*rush_yd_pts + rushing_tds*rush_td_pts + receiving_yards*rec_yd_pts + receiving_tds*rec_td_pts + fumbles_lost*fumble_lost_pts + 0.4*(rushing_first_downs + receiving_first_downs)`

`expected_lve_points = pass_yards_exp*pass_yd_pts + pass_td_exp*pass_td_pts + pass_int_exp*int_pts + rush_yards_exp*rush_yd_pts + rush_td_exp*rush_td_pts + rec_yards_exp*rec_yd_pts + rec_td_exp*rec_td_pts + 0.4*(rush_first_down_exp + rec_first_down_exp)`

If you cannot build a defensible expected-turnover model, leave turnover expectation out of `expected_lve_points` and keep turnovers inside the historical/efficiency layer only.

### Recency rule

Use a strict three-season recency blend on every season-level stat:

`recency_blend = 0.55*Y0 + 0.30*Y-1 + 0.15*Y-2`

If a season is missing, redistribute weight proportionally across available seasons.

Use **active-game** rates, not season totals:

- QB active game: `pass_attempts + rush_attempts >= 8`
- RB active game: `snap_share >= 15%`
- WR/TE active game: `snap_share >= 25%`

### Shrinkage rule for noisy rates

For every raw rate, use empirical-Bayes shrinkage before normalization:

`shrunk_rate = (opp / (opp + k)) * raw_rate + (k / (opp + k)) * historical_pos_mean`

Recommended `k` values:

- QB attempt-based rates: `k = 250`
- QB rush-based rates: `k = 80`
- RB carry/target rates: `k = 150`
- RB TD / first-down rates: `k = 200`
- WR target-share / air-share / FD-rate: `k = 90`
- WR TD-rate: `k = 120`
- TE target-share / FD-rate: `k = 70`
- TE TD-rate: `k = 100`

### 0–100 transformation

Use fixed training distributions from **2018–2025 qualified player-seasons**:

`norm(feature) = 100 * percentile_rank_pos_feature(winsorized_feature)`

Winsorize at the 2.5th and 97.5th percentiles within position and feature.  
For “lower is better” fields, invert:

`norm_inverse(feature) = 100 - norm(feature)`

### Age score

Age belongs in dynasty-hold and keeper logic more than private value.

**QB age score**
- Pocket archetype: `<=24:80, 25-27:92, 28-31:100, 32:94, 33:88, 34:80, 35+:68`
- Dual-threat archetype: `<=24:90, 25-27:100, 28:94, 29:84, 30:72, 31:58, 32+:42`

Define dual-threat as:
`projected_rush_points_pg >= 3.0` or `rush_attempts_pg >= 5`

**RB age score**
- `21-22:86, 23:94, 24-25:100, 26:90, 27:76, 28:60, 29:42, 30+:24`

**WR age score**
- `21-22:82, 23-26:100, 27:94, 28:86, 29:72, 30:58, 31:42, 32+:28`

**TE age score**
- `22-24:78, 25-28:100, 29:92, 30:82, 31:68, 32:52, 33+:36`

### Injury durability score

Because the nflverse injury feed currently has no 2025 data, durability should use a conservative fallback rather than pretending the injury layer is complete. citeturn5view7

**Model-design choice**

`durability_score = 50*games_played_share_last_2y + 20*high_snap_game_share_last_2y + 20*(1 - long_absence_share_last_2y) + 10*current_health_flag`

Where:
- `games_played_share_last_2y = games_played / team_games`
- `high_snap_game_share_last_2y = games with >=50% snaps / games_played`
- `long_absence_share_last_2y = games missed in absences of 3+ straight games / team_games`
- `current_health_flag = 1.0 healthy, 0.5 routine rehab/questionable offseason, 0.0 active severe uncertainty`

If you do **not** have a reliable current-health feed, set `current_health_flag = 0.5` and cap the final durability score at `85`.

## Position-specific formulas

### Bucket definitions

Use these abbreviations:

- `H` = historical LVE scoring
- `X` = expected fantasy/opportunity
- `R` = role / security / usage
- `E` = target earning / workload earning
- `F` = first-down / chain-moving / TD fit
- `EFF` = efficiency
- `P` = projection
- `A` = age curve
- `D` = injury durability
- `C` = confidence
- `M` = market liquidity only

Use these helper components:

- `ALPG` = normalized actual LVE points per active game, recency-blended
- `XLPG` = normalized expected LVE points per active game, recency-blended
- `LAST8` = normalized last-8 active-game actual LVE PPG
- `TS` = normalized target share
- `AYS` = normalized air-yard share
- `RSH` = normalized rush share
- `XSH` = normalized expected-opportunity share within position group
- `FDG` = normalized first downs per active game
- `FDR` = normalized first downs per opportunity
- `TDX` = normalized expected TDs per game
- `EPOE` = normalized actual minus expected LVE points per active game
- `CSC` = contract security score
- `ROLE` = depth-chart role score

### Quarterback

**Model-design choice**

`H_QB   = 0.70*ALPG + 0.30*LAST8`  
`X_QB   = 0.70*XLPG + 0.30*dropback_share_score`  
`R_QB   = 0.55*starter_share_score + 0.25*CSC + 0.20*ROLE`  
`E_QB   = 0.70*dropback_share_score + 0.30*designed_rush_share_score`  
`F_QB   = 0.50*pass_first_down_pg_score + 0.20*rush_first_down_pg_score + 0.30*pass_td_exp_pg_score`  
`EFF_QB = 0.40*qbr_score + 0.35*EPOE + 0.25*pass_first_down_diff_pg_score`  
`P_QB   = projected_lve_ppg_score`

`private_pre_QB = 0.18*H_QB + 0.18*X_QB + 0.16*R_QB + 0.08*E_QB + 0.12*F_QB + 0.14*EFF_QB + 0.06*P_QB + 0.04*A_QB + 0.04*D_QB`

`elite_qb_exception = 1 if (projected_lve_ppg - QB14_projected_lve_ppg >= 5.0) and (projected_rush_points_pg >= 3.0 or qbr_score >= 85) else 0`

`private_lve_value_QB = clamp(private_pre_QB - 10 + 10*elite_qb_exception, 0, 100)`

`win_now_value_QB      = 0.45*private_lve_value_QB + 0.20*P_QB + 0.10*R_QB + 0.10*D_QB + 0.10*EFF_QB + 0.05*C_QB`

`dynasty_hold_value_QB = 0.46*private_lve_value_QB + 0.20*A_QB + 0.12*R_QB + 0.10*D_QB + 0.12*C_QB`

`keeper_score_QB       = 0.50*dynasty_hold_value_QB + 0.20*win_now_value_QB + 0.15*C_QB + 0.15*VOR_QB - forced_release_penalty`

`drop_candidate_score_QB = 0.65*(100 - keeper_score_QB) + 0.20*(100 - C_QB) + 0.15*(100 - M_QB)`

`trade_value_QB        = 0.50*dynasty_hold_value_QB + 0.20*win_now_value_QB + 0.20*M_QB + 0.10*C_QB`

`market_edge_score_QB  = clamp(50 + 0.70*(private_lve_value_QB - market_rank_score_QB) + 0.30*(M_QB - 50), 0, 100)`

`confidence_score_QB   = 0.35*sample_score_QB + 0.20*role_clarity_QB + 0.15*health_clarity_QB + 0.15*projection_agreement_QB + 0.15*stability_QB`

### Running back

**Model-design choice**

`H_RB   = 0.60*ALPG + 0.20*LAST8 + 0.20*VOR_RB`  
`X_RB   = 0.60*XLPG + 0.25*XSH + 0.15*rush_first_down_exp_pg_score`  
`R_RB   = 0.35*snap_share_score + 0.25*ROLE + 0.20*CSC + 0.20*backfield_share_score`  
`E_RB   = 0.50*XSH + 0.30*team_rush_share_score + 0.20*target_share_score`  
`F_RB   = 0.45*rush_first_down_pg_score + 0.25*rush_first_down_per_carry_score + 0.30*TDX`  
`EFF_RB = 0.45*EPOE + 0.35*ryoe_per_att_score + 0.20*rush_first_down_diff_pg_score`  
`P_RB   = projected_lve_ppg_score`

`private_pre_RB = 0.20*H_RB + 0.20*X_RB + 0.14*R_RB + 0.16*E_RB + 0.10*F_RB + 0.08*EFF_RB + 0.04*P_RB + 0.05*A_RB + 0.03*D_RB`

`private_lve_value_RB = clamp(private_pre_RB, 0, 100)`

`rb_fragility_penalty = min(20, max(0, 0.04*(weighted_touches_last_2y - 500)) + 6*major_lower_body_event_count_last_2y)`

`win_now_value_RB      = 0.38*private_lve_value_RB + 0.20*P_RB + 0.15*R_RB + 0.12*X_RB + 0.10*F_RB + 0.05*D_RB`

`dynasty_hold_value_RB = clamp(0.34*private_lve_value_RB + 0.18*A_RB + 0.14*R_RB + 0.12*D_RB + 0.10*E_RB + 0.12*C_RB - rb_fragility_penalty, 0, 100)`

`keeper_score_RB       = 0.44*dynasty_hold_value_RB + 0.28*win_now_value_RB + 0.12*C_RB + 0.16*VOR_RB - forced_release_penalty`

`drop_candidate_score_RB = 0.55*(100 - keeper_score_RB) + 0.20*rb_fragility_penalty + 0.15*(100 - C_RB) + 0.10*(100 - M_RB)`

`trade_value_RB        = 0.42*dynasty_hold_value_RB + 0.28*win_now_value_RB + 0.20*M_RB + 0.10*C_RB`

`market_edge_score_RB  = clamp(50 + 0.70*(private_lve_value_RB - market_rank_score_RB) + 0.30*(M_RB - 50), 0, 100)`

`confidence_score_RB   = 0.25*sample_score_RB + 0.25*role_clarity_RB + 0.20*health_clarity_RB + 0.15*projection_agreement_RB + 0.15*workload_stability_RB`

### Wide receiver

**Model-design choice**

`H_WR   = 0.55*ALPG + 0.25*LAST8 + 0.20*VOR_WR`  
`X_WR   = 0.55*XLPG + 0.25*rec_first_down_exp_pg_score + 0.20*AYS`  
`R_WR   = 0.35*snap_share_score + 0.25*ROLE + 0.20*CSC + 0.20*team_pass_role_score`  
`E_WR   = 0.45*TS + 0.30*AYS + 0.25*target_share_over_snap_share_score`  
`F_WR   = 0.45*rec_first_down_pg_score + 0.25*rec_first_down_per_target_score + 0.30*TDX`  
`EFF_WR = 0.35*EPOE + 0.25*rec_yards_diff_pg_score + 0.20*separation_score + 0.20*yac_oe_score`  
`P_WR   = projected_lve_ppg_score`

`private_pre_WR = 0.18*H_WR + 0.18*X_WR + 0.14*R_WR + 0.18*E_WR + 0.12*F_WR + 0.10*EFF_WR + 0.04*P_WR + 0.04*A_WR + 0.02*D_WR`

`private_lve_value_WR = clamp(private_pre_WR + 5, 0, 100)`

`win_now_value_WR      = 0.40*private_lve_value_WR + 0.18*P_WR + 0.15*E_WR + 0.12*R_WR + 0.10*F_WR + 0.05*D_WR`

`dynasty_hold_value_WR = 0.42*private_lve_value_WR + 0.22*A_WR + 0.14*E_WR + 0.08*R_WR + 0.06*D_WR + 0.08*C_WR`

`keeper_score_WR       = 0.46*dynasty_hold_value_WR + 0.24*win_now_value_WR + 0.12*C_WR + 0.18*VOR_WR - forced_release_penalty`

`drop_candidate_score_WR = 0.70*(100 - keeper_score_WR) + 0.20*(100 - C_WR) + 0.10*(100 - M_WR)`

`trade_value_WR        = 0.46*dynasty_hold_value_WR + 0.22*win_now_value_WR + 0.22*M_WR + 0.10*C_WR`

`market_edge_score_WR  = clamp(50 + 0.70*(private_lve_value_WR - market_rank_score_WR) + 0.30*(M_WR - 50), 0, 100)`

`confidence_score_WR   = 0.30*sample_score_WR + 0.20*role_clarity_WR + 0.15*health_clarity_WR + 0.15*projection_agreement_WR + 0.20*target_stability_WR`

### Tight end

**Model-design choice**

`H_TE   = 0.55*ALPG + 0.25*LAST8 + 0.20*VOR_TE`  
`X_TE   = 0.50*XLPG + 0.30*rec_first_down_exp_pg_score + 0.20*TDX`  
`R_TE   = 0.30*snap_share_score + 0.25*route_rate_proxy_score + 0.20*ROLE + 0.15*CSC + 0.10*TS`  
`E_TE   = 0.45*TS + 0.25*target_share_over_snap_share_score + 0.15*AYS + 0.15*route_rate_proxy_score`  
`F_TE   = 0.50*rec_first_down_pg_score + 0.20*rec_first_down_per_target_score + 0.30*TDX`  
`EFF_TE = 0.35*EPOE + 0.25*rec_first_down_diff_pg_score + 0.25*yprr_proxy_score + 0.15*separation_score`  
`P_TE   = projected_lve_ppg_score`

`private_pre_TE = 0.18*H_TE + 0.16*X_TE + 0.18*R_TE + 0.18*E_TE + 0.14*F_TE + 0.08*EFF_TE + 0.04*P_TE + 0.02*A_TE + 0.02*D_TE`

`elite_te_exception = 1 if (projected_lve_ppg - TE14_projected_lve_ppg >= 4.0) and (TS >= 75 or route_rate_proxy_score >= 80) else 0`

`private_lve_value_TE = clamp(private_pre_TE - 8 + 6*elite_te_exception, 0, 100)`

`win_now_value_TE      = 0.40*private_lve_value_TE + 0.18*P_TE + 0.16*R_TE + 0.11*E_TE + 0.10*F_TE + 0.05*D_TE`

`dynasty_hold_value_TE = 0.40*private_lve_value_TE + 0.20*A_TE + 0.16*R_TE + 0.08*E_TE + 0.08*D_TE + 0.08*C_TE`

`keeper_score_TE       = 0.48*dynasty_hold_value_TE + 0.20*win_now_value_TE + 0.14*C_TE + 0.18*VOR_TE - forced_release_penalty`

`drop_candidate_score_TE = 0.68*(100 - keeper_score_TE) + 0.20*(100 - C_TE) + 0.12*(100 - M_TE)`

`trade_value_TE        = 0.44*dynasty_hold_value_TE + 0.20*win_now_value_TE + 0.26*M_TE + 0.10*C_TE`

`market_edge_score_TE  = clamp(50 + 0.70*(private_lve_value_TE - market_rank_score_TE) + 0.30*(M_TE - 50), 0, 100)`

`confidence_score_TE   = 0.25*sample_score_TE + 0.25*role_clarity_TE + 0.15*health_clarity_TE + 0.15*projection_agreement_TE + 0.20*route_target_stability_TE`

### League replacement lines and market-only definitions

**Model-design choice**

Use these replacement baselines for LVE:

- `QB14`
- `RB30`
- `WR46`
- `TE14`

Then:

`VOR_pos = clamp(50 + 10*(projected_lve_ppg - replacement_lve_ppg_pos), 0, 100)`

For market-only logic:

`market_rank_score_pos = 100 * (1 - (market_rank_pos - 1)/(market_cap_pos - 1))`

Use:
- `market_cap_QB = 40`
- `market_cap_RB = 90`
- `market_cap_WR = 120`
- `market_cap_TE = 40`

If you do not have true trade-volume data, use deterministic liquidity priors:

- `QB: 45`
- `RB: 80`
- `WR: 88`
- `TE: 55`

Then:

`M_pos = 0.70*market_rank_score_pos + 0.30*liquidity_prior_pos`

This keeps market data at **0% of private/stat value** and only inside trade execution / market-edge layers.

## League-specific rules and guardrails

### QB suppression in 1QB

**Evidence-backed finding:** public replacement-level work and late-round-QB strategy both point to a high QB replacement level, while format-specific WAR work does not treat ordinary QBs as dominant assets in typical 1QB settings. citeturn19search4turn19search13turn18search2

**Model-design choice**

- Apply a flat `-10` private-value context adjustment to all QBs.
- Remove that suppression only for the **elite QB exception**.
- Require a **5.0+ projected LVE PPG edge over QB14** to call a QB elite.
- Dual-threat QBs age faster than pocket passers, so dynasty-hold should use the dual-threat age table where applicable.

### RB role versus dynasty fragility

**Evidence-backed finding:** RB opportunity is more predictive than raw touches, and RBs age out earlier than WRs. citeturn30search2turn15search0turn13search6

**Model-design choice**

- Make RB private value heavily usage- and opportunity-driven.
- Make dynasty-hold explicitly penalize heavy recent touch counts and injury fragility.
- In ties, prefer the RB with stronger expected-opportunity share and better first-down/TD fit over the RB with a small efficiency edge.

### WR target earning and 3WR/2flex demand

**Evidence-backed finding:** target-based receiver metrics are stronger than raw routes alone, and first-down-based receiving work adds useful forward signal. Your lineup structure also creates unusually deep WR demand. citeturn29view4turn29view3turn17search4turn18search2

**Model-design choice**

- Give WRs a `+5` private-value context adjustment.
- Weight `E_WR` and `F_WR` more heavily than raw efficiency.
- Treat WRs with strong target share, air-yard share, and first-down conversion rates as the preferred dynasty-hold archetype.

### TE no-premium suppression

**Evidence-backed finding:** non-elite TEs derive value from route involvement and real receiving roles, but non-premium formats suppress the whole middle class of the position. citeturn31search2turn31search12turn18search2

**Model-design choice**

- Apply a flat `-8` context adjustment to all TEs.
- Only allow an elite TE to recover most of that penalty if he projects **4.0+ LVE PPG over TE14** and has top-end target/route involvement.
- Never let generic TE “scarcity” override no-premium economics.

### Rejected features and double-counting traps

**Model-design choice**

Do **not** include the following inside private/stat value:

- ADP, dynasty trade calculators, startup market prices, or expert rank consensus.
- Raw fantasy points **and** raw yards/TDs/first downs all at full weight.
- YPRR, targets per route, target share, and yards per target all together at full weight.
- Snap share, route participation, and route count all together at full weight.
- Actual TDs and xTD at full weight inside multiple buckets.
- Injury designation, games missed, and durability penalties all stacked separately without consolidation.
- Draft capital for veterans after Year 2, except as a minor role-security tiebreaker if you explicitly want it.
- The default PPR-based `total_fantasy_points` fields from expected-points tables for this no-PPR league. citeturn8view0

## Sanity fixtures

These are **model-design expectations**. If your implementation violates these, something is probably wrong.

For entity["athlete","Kyren Williams","NFL running back"] versus entity["athlete","Bijan Robinson","NFL running back"], entity["athlete","Jahmyr Gibbs","NFL running back"], and entity["athlete","Ashton Jeanty","NFL running back"], the default output should be: **Bijan/Gibbs above Kyren in all major scores; Kyren above Jeanty in private_lve_value and win_now_value; Jeanty can close the gap in dynasty_hold_value but should not clear Kyren solely on youth.** The public evidence supports that ordering: Kyren was 25 with 1,252 rushing yards and 10 rushing TDs in 2025; Bijan was 24 coming off 2,298 scrimmage yards in 2025; Gibbs was 24 with 1,223 rushing yards and 13 rushing TDs in 2025; Jeanty was 22 and productive as a rookie, but his 2025 output was still below those veteran win-now profiles. citeturn24search6turn24search2turn23news21turn22search2turn22search6turn25search0turn25search2turn22search14

For entity["athlete","Jaxon Smith-Njigba","NFL wide receiver"] versus entity["athlete","Tee Higgins","NFL wide receiver"], the model should return **JSN clearly over Higgins** in private value, dynasty hold, and usually win-now. JSN was 24 and posted 119 receptions, 1,793 yards, and 10 TDs in 2025; Higgins was 27 and produced 59 receptions, 846 yards, and 11 TDs in 2025, with public reporting also flagging recent missed-game and concussion concerns. A stats-first model should prioritize JSN’s much stronger target-earning and yardage profile here. citeturn21search0turn24search1turn22search0turn22search8turn22search15

For entity["athlete","Brian Thomas Jr.","NFL wide receiver"] versus entity["athlete","Luther Burden III","NFL wide receiver"], the model should return **BTJ over Burden** across private_lve_value, dynasty_hold_value, keeper_score, and trade_value. Thomas was 23 and already had an elite 2024 rookie year on top of a 2025 line of 48 receptions for 707 yards; Burden was 22 and had a respectable but clearly smaller 2025 rookie line of 47 receptions for 652 yards and 2 TDs. Burden can win **market_edge_score** only if market price lags his internal projection; he should not win the underlying private/stat stack on current NFL evidence. citeturn24search0turn24search4turn20search2turn20search12turn20search1turn20search8

For entity["athlete","Chase Brown","NFL running back"] versus entity["athlete","Luther Burden III","NFL wide receiver"], the model should return **Brown over Burden in private_lve_value and win_now_value**, and usually in keeper_score for contending builds. Brown was 26 and cleared 1,019 rushing yards in 2025; Burden’s rookie receiving line was useful, but your format is no-PPR with a first-down bonus, and Brown’s immediate workload profile is more actionable. Burden can narrow or beat Brown only in pure dynasty-hold if Brown’s role certainty deteriorates materially. citeturn21search3turn21search7turn21search19turn20search1

For the **elite QB exception**, the model should only allow a QB to break through suppression if he meaningfully separates from QB14 on projected LVE scoring and carries real rushing or efficiency edge. Ordinary QB1s should not outscore comparable WR/RB assets in keeper or trade value merely because they are quarterbacks. That is the point of the 1QB suppression layer. citeturn19search4turn19search13turn18search2

For **no-premium TE suppression**, a non-elite TE should almost never outrank a comparable WR25/RB25 profile in dynasty-hold or trade value. If your TE bucket is pushing generic midrange TEs above strong WR depth, the implementation is over-crediting position scarcity. citeturn31search2turn31search12turn18search2

## Calibration and backtesting

**Model-design choice**

Use a rolling, season-forward backtest.

### Historical train/validation/test windows

- Train: 2018–2023
- Validate: 2024
- Test: 2025
- Refit annually after each season

### Targets

Backtest each output against a target that matches its purpose:

- `private_lve_value` → next-season LVE points per active game
- `win_now_value` → same-season total LVE points above replacement
- `dynasty_hold_value` → two-year discounted LVE production
- `keeper_score` → top-230 roster survival plus starter-value retention
- `drop_candidate_score` → next 12 months of roster-cut probability
- `trade_value` → blended next-year + two-year discounted production, with liquidity only affecting execution score
- `confidence_score` → calibration of absolute error bands

### Metrics

Use:
- Spearman rank correlation
- MAE on next-season LVE PPG
- Brier score for categorical outcomes such as top-12 / top-24 / top-36 finishes
- Calibration plots by confidence decile
- Error slicing by position, age bucket, injury bucket, and sample bucket

### What to tune

Tune only:
- bucket weights
- shrinkage `k` values
- replacement-line choices
- RB fragility penalty coefficients
- elite QB / elite TE thresholds

Do **not** tune against market outcomes.

### Pass/fail criteria

A good first release should satisfy all of the following:

- Outperform a trailing-points-only baseline
- Outperform an xLVE-only baseline
- Improve WR and RB rank stability
- Reduce rookie/young-player overrating when NFL sample is weak
- Preserve elite QB and elite TE exceptions without inflating the middle class

## Schema and source links

### Recommended CSV layout

Use three primary files.

#### `lve_player_inputs.csv`
One row per player per snapshot date.

Required columns:

- `snapshot_date`
- `season`
- `week`
- `player_id_gsis`
- `player_id_mfl`
- `player_id_fantasypros`
- `player_name`
- `position`
- `team`
- `age`
- `contract_years_remaining`
- `actual_lve_points_pg`
- `expected_lve_points_pg`
- `snap_share`
- `target_share`
- `air_yard_share`
- `rush_share`
- `rush_first_down_pg`
- `rec_first_down_pg`
- `rush_first_down_per_opp`
- `rec_first_down_per_target`
- `pass_first_down_pg`
- `xop_share_pos`
- `epoe_pg`
- `qbr`
- `ryoe_per_att`
- `separation`
- `yac_oe`
- `projected_lve_points_pg`
- `games_played_last_2y`
- `games_missed_last_2y`
- `long_absence_count_last_2y`
- `current_health_flag`
- `market_rank_pos`
- `forced_release_flag`

Use the nflverse fantasy-ID crosswalk for IDs; the public dictionary notes that `mfl_id` is the complete primary key for that table, and it also provides GSIS and FantasyPros mappings. citeturn7search10

#### `lve_bucket_scores.csv`
One row per player per snapshot date.

Columns:

- `player_id_gsis`
- `snapshot_date`
- `H_score`
- `X_score`
- `R_score`
- `E_score`
- `F_score`
- `EFF_score`
- `P_score`
- `A_score`
- `D_score`
- `M_score`
- `VOR_score`
- `confidence_score`

#### `lve_model_outputs.csv`
One row per player per snapshot date.

Columns:

- `player_id_gsis`
- `snapshot_date`
- `private_lve_value`
- `win_now_value`
- `dynasty_hold_value`
- `keeper_score`
- `drop_candidate_score`
- `trade_value`
- `market_edge_score`
- `confidence_score`
- `position_context_note`
- `elite_exception_flag`

### Open questions and limitations

The model is coding-ready, but four things are still parameterized because the public evidence does not fully resolve them:

- Your exact passing/turnover scoring settings were not specified, so the formulas intentionally use configurable scoring constants.
- The phrase “forced league-rank top-five release rule” is ambiguous. I assumed you can encode it as a binary `forced_release_flag`; if your rule works differently, that flag logic should be changed without changing the rest of the model.
- nflverse injury data currently has a post-2024 gap, so durability is necessarily more conservative unless you add a separate current-health feed. citeturn5view7
- Public live route-participation data is less clean than the old stack, so `route_rate_proxy` is included as a fallback field rather than a guaranteed nflverse-native metric. citeturn5view7turn26view0

### Source links

Core public sources for implementation and validation:

- urlnflreadr docsturn10search1
- urlffopportunity docsturn0search13
- urlnflverse GitHub organizationhttps://github.com/nflverse
- urlOverTheCap contract historyhttps://overthecap.com/contract-history
- urlPro Football Reference advanced receiving tableshttps://www.pro-football-reference.com/years/2025/receiving_advanced.htm
- urlESPN QBR leaders and definitionhttps://www.espn.com/nfl/qbr