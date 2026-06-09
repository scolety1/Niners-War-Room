# Phase 10O Formula Requirements Lock

Date: 2026-05-17

## Purpose

Phase 10O converts the preserved Deep Research and external audit reports into pre-formula requirements for Model v4. This document is a design lock, not a scoring implementation. It must inform later formula work, but it must not become player evidence, a ranking source, or an app-promotion gate by itself.

No formula scores, active rankings, My Team surfaces, War Board surfaces, or readiness gates were changed in this phase.

## Inputs Reviewed

Primary research and intake documents:

- `docs/model_v4/PHASE_10J_EXTERNAL_RESEARCH_INTAKE.md`
- `docs/model_v4/DEEP_RESEARCH_SIGNAL_TRIAGE.md`
- `docs/model_v4/DEEP_RESEARCH_SIGNAL_TRIAGE.csv`
- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-26-audit-framework.md`
- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-27-rookie-signals.md`
- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-28-inline-position-signals-summary.md`

Phase 10 external reports:

- `Audit Checklist for a Local-First Dynasty Fantasy Football Data Pipeline.md`
- `Auditing a Dynasty Rookie Draft Model Data Stack.md`
- `deep-research-report (26).md`
- `deep-research-report (27).md`
- `Modeling First-Down and Return Scoring in Dynasty Fantasy Football.md`
- `Replacement-Level Value and VORP for a 10-Team 1QB Dynasty Fantasy Football League.md`
- `Rookie Metric Framework for a Local-First Dynasty Analyzer.md`
- `Veteran Dynasty Decision Framework.md`
- `PHASE10_EXTERNAL_REPORTS_MANIFEST.csv`

## Research Admission Rule

The reports are admitted as formula-design guidance only.

They are not:

- player evidence rows
- source production rows
- market inputs
- projections
- formula weights that must be copied exactly
- final rankings

Later formula phases may use the signal hierarchy and guardrails in this document, but every player-level value must still come from admitted factual evidence, derived evidence, prospect-prior evidence, context lanes, and receipts already governed by the Model v4 source contracts.

## Global Formula Target

Model v4 must value players for:

- 10-team dynasty
- 1QB
- non-PPR
- rushing and receiving first-down scoring
- no TE premium
- return yards at 1 point per 30 yards
- return TDs at 4 points

The formula target is league-adjusted value above replacement, not raw fantasy points and not generic dynasty market value.

Required structure:

```text
private_football_value = f(admitted production, admitted usage, age/lifecycle, admitted prospect priors, replacement/VORP)
market_context = separate context layer only
projection_context = separate context layer only
decision_output = private football value + explicit context/review labels, never hidden leakage
```

## Position Signal Hierarchy

### RB

Required priority order:

1. Role and opportunity: snap share, carry share, touch share, routes, target role, and weighted opportunities.
2. First-down workload: rushing first downs, receiving first downs, team first-down share, first downs per game, and regressed first-down rate.
3. Red-zone and goal-line role: high-value touches, short-yardage usage, and TD expectation inputs.
4. Receiving utility: targets, routes, receiving first downs, yards per route, and passing-down role. This remains valuable even in non-PPR because it predicts field time and three-down ceiling.
5. Age, survival, durability, and workload fragility.
6. Efficiency only after volume support: yards after contact, broken tackles, success context, and explosive ability must be shrunk and cannot outrank role.

Required RB formula guardrails:

- RB value must be short-window and role-driven.
- RB future value must discount faster than WR, TE, and QB.
- RBs age 27+ need stronger receipts to hold high dynasty value.
- Yards per carry, TD spikes, and small-sample explosive efficiency cannot drive an elite score.
- Missing receiving-role evidence cannot become neutral or positive evidence.
- Non-PPR shifts some weight toward rushing, goal-line, and first-down conversion, but it does not eliminate receiving role.

### WR

Required priority order:

1. Target earning: target share, targets per route run, target volume, and team target context.
2. Route evidence: routes run, route participation where valid, and stable route opportunity.
3. Route-based production: YPRR, first downs per route, receiving yards per route, and team-adjusted efficiency.
4. First-down and yardage production: receiving first downs, first downs per game, receiving yards per game, and team receiving first-down share.
5. Air-yard role: air-yards share, WOPR-style profile, downfield role, and route depth context.
6. Age curve and ecosystem: WR prime should be longer than RB but decline risk rises after the late 20s and especially in the 30+ range.

Required WR formula guardrails:

- WR value must favor target earning and route participation over TDs, catch rate, raw yards per target, or unsupported vacated-target assumptions.
- Possession and chain-moving WRs should gain relative to empty-catch PPR profiles.
- Deep-threat efficiency alone cannot create elite value without route and target volume.
- WR age decline should be less harsh than RB decline, but old catch-volume-only profiles need format friction in non-PPR.
- Licensed RotoWire routes, TPRR, YPRR, target share, air-yards share, and alignment evidence may be used only when admitted and source-labeled.

### QB

Required priority order:

1. VORP above 10-team 1QB replacement, not raw QB points.
2. Rushing production: designed rushes, scrambles, rushing yards, rushing attempts, rushing first downs, and red-zone rushing.
3. Passing volume and job security: attempts, dropbacks, starter runway, contract/draft context where admitted, and offense stability.
4. Passing production and expected TD context.
5. Efficiency as regression and fragility context, not as a primary fantasy driver.
6. Age/archetype split: pocket passers age differently from rushing QBs.

Required QB formula guardrails:

- 1QB format must suppress replaceable QB production.
- Non-rushing QB6-QB12 profiles cannot outrank elite RB/WR assets unless VORP proves a real league-specific edge.
- Rushing QBs may retain elite value only when the replacement gap is real.
- Rushing-age caution must apply around age 29-31. Rushing value should not be projected as permanent.
- Lamar Jackson type players require a passing-floor receipt once rushing decline risk appears. The correct model behavior is not automatic sell, but "sell only at premium" or similar review language if the market pays for peak rushing forever.

### TE

Required priority order:

1. Route participation and real route-running role.
2. Target earning and top-2 team target status.
3. YPRR, first downs per route, receiving first downs, and receiving yards.
4. VORP edge over no-premium TE replacement.
5. Age/development context.
6. Red-zone role and TD expectation as secondary, heavily regressed context.

Required TE formula guardrails:

- No structural TE premium is allowed.
- Snap share without routes is not receiving evidence.
- TD-only TE production cannot create durable elite dynasty value.
- TE breakout-age heuristics are weaker than WR breakout-age heuristics.
- A TE should receive cross-position premium only when route/target dominance creates a real no-premium VORP gap.
- Young TE patience must be bounded; "TEs take time" cannot justify low-evidence profiles indefinitely.

## Rookie And Prospect Signal Hierarchy

Rookie/prospect value must remain separate from veteran NFL production value.

Required priority order:

1. Draft capital as the strongest starting prior after the draft has occurred.
2. Age-adjusted and share-adjusted college production.
3. Position-specific usage and efficiency:
   - RB: rushing share, receiving role, yards after contact, broken tackles, goal-line profile, functional size/speed.
   - WR: target earning, market share, YPRR, receiving yards per team pass attempt, breakout age, early declare.
   - QB: Round 1 or premium draft capital, rushing, passing efficiency, sack avoidance, young-for-class status.
   - TE: draft capital, receiving production/share, YPRR or adjusted yards per play, athleticism, route/target profile.
4. Athletic testing as a position-specific prior and tie-breaker, strongest for RB/TE, more modest for WR, and limited for QB except rushing/mobility context.
5. Landing spot and depth chart as capped short-run modifiers, not long-run player-quality engines.
6. Injury history as a confidence and availability modifier.
7. Market/ADP/rankings only as context, residual, and trade timing information.

Required rookie/prospect guardrails:

- Draft capital must use a nonlinear or tiered transform; raw pick number cannot be treated as a linear feature.
- Draft capital decays as NFL evidence arrives:
  - rookie preseason: 100% prior
  - after Year 1: about 45%
  - after Year 2: about 20%
  - after Year 3: about 5%
- Draft capital remains a prior, not a verdict.
- 10-team 1QB format must tax rookie QBs unless the profile is elite and fantasy-rushing relevant.
- No-premium TE format must tax ordinary TE prospects unless they clear premium draft-capital and receiving-profile bars.
- Missing route, target, injury, combine, or source-ID evidence must cap confidence; it cannot increase a player.
- Prospect formulas must be validated against draft-capital-only and market-only baselines before being trusted.
- Historical rookie backtests must be time-safe, identity-safe, and leave-one-draft-class-out or walk-forward validated.

## Veteran And Aging Rules

Age is a burden-of-proof prior, not an automatic verdict.

Default age lanes:

| Archetype | Reliable Prime | First Caution Lane | Default Decline Lane |
| --- | ---: | ---: | ---: |
| RB | 24-28 | 29 | 30+ |
| WR | 25-31 | 32 | 33+ |
| Pocket-leaning QB | 26-31 | 32-33 | 34+ |
| Elite rushing QB | 24-28 | 29-30 | 31+ |
| TE | 26-32 | 33-34 | 35+ |

Required veteran guardrails:

- Older players need receipts, not name value.
- Veterans in caution lanes need at least two positive receipts for strong hold labels.
- Veterans in red age lanes need at least three positive receipts for "sell only at premium" style labels.
- At least one receipt must be a sticky role metric.
- At least one receipt must be a health/durability clearance.
- TD-driven production requires an extra receipt.
- Injury and workload risk should lower confidence, not fabricate zero value.
- Private football value and market liquidity must stay separate.

Required veteran fixture archetypes:

- Aging RB outlier who still owns role and first-down value should not be auto-crushed if current contender value is real.
- Aging WR with catch-volume but weak first-down/chunk/TD insulation should be easier to shop in this non-PPR format.
- Elite rushing QB age 29-31 should require passing-floor receipts.
- Older elite TE should be contender-useful only if he still creates real weekly no-premium separation.

## First-Down Scoring Rules

First downs are core scoring evidence in this league.

Required rules:

- Use direct rushing and receiving first-down fields where imported and admitted.
- Mark direct first-down fields as `imported_real_data`.
- Any yardage-derived first-down fallback must be labeled as estimated, reviewable, and lower confidence.
- Estimated first downs must never overwrite direct first-down data.
- Penalty first downs and team-level first downs must not be credited to players.
- QB scrambles that earn first downs are rushing first downs, not passing first downs.
- First-down volume and share should matter more than first-down rate.
- First-down rate must be regressed, especially for RB rushing and low-sample receiving profiles.
- Avoid double counting yardage and first downs. First-down scoring is real, but much of it is correlated with yardage.

Required first-down module direction:

| Use Case | First Downs Per Game/Projected Total | Team First-Down Share | Regressed First-Down Rate |
| --- | ---: | ---: | ---: |
| Seasonal projection | 45% | 35% | 20% |
| Dynasty talent/role score | 30% | 50% | 20% |

These are research-backed starting requirements for the later formula phase, not implemented coefficients in Phase 10O.

## Return Scoring Rules

Return scoring is direct scoring evidence, not a durable talent engine.

Required rules:

- Keep kick returns and punt returns separate where possible.
- Treat return production as current-year or near-term role evidence.
- Return yards and return TDs may enter direct scoring only after matched identity admission.
- Return production must not become a major talent signal or long-horizon role signal.
- Return TDs must be heavily regressed.
- Return-era context matters because NFL kickoff rules changed materially in 2024 and 2025.
- Future return value must decay quickly unless a player has repeat proof and stable team role.

Required return caps:

- Return production should usually break ties, boost fringe starters, or create short windows of value.
- Return value should not let return-only players leapfrog real offensive starters with stable role evidence.
- Return contribution should remain small and explicitly labeled as direct scoring evidence.

## VORP And Replacement Rules

The final Model v4 formula must use replacement-adjusted value.

Required baseline concepts:

- Maintain both starter-side value and waiver/roster-side value.
- Keep signed internal values; presentation may clamp to zero only after decision logic has access to negative values.
- Replacement baselines must be configurable by league size, lineup slots, flex usage, and bench depth.
- Default 10-team 1QB starting assumptions can use approximately:
  - QB starter baseline: QB11-QB12
  - QB waiver/roster baseline: QB17-QB20
  - RB starter baseline: RB28-RB30
  - RB waiver/roster baseline: RB55-RB65
  - WR starter baseline: WR31-WR34
  - WR waiver/roster baseline: WR58-WR70
  - TE starter baseline: TE10-TE11
  - TE waiver/roster baseline: TE17-TE20

Required formulas to support later:

```text
VOLS = ProjectedPoints - StarterReplacementPoints
VORP = ProjectedPoints - WaiverReplacementPoints
SignedBenchValue = VORP
PublishedVORP = max(0, VORP)
```

Availability-aware variants must give replacement credit for missed games rather than treating missed weeks as pure zeroes:

```text
AvailableAdjustedPoints =
  ExpectedGames * PlayerPPG
  + (ScheduleWeeks - ExpectedGames) * WeeklyReplacementPoints
```

QB-specific requirement:

- Split passing and rushing value when possible.
- Suppress replaceable passing value.
- Preserve rushing value only when it creates a real 1QB replacement gap.

TE-specific requirement:

- No automatic TE premium.
- TE value comes from no-premium VORP gap only.
- Rookie/young TE role ramps may exist but must widen uncertainty.

## Source And Leakage Guardrails

These are hard formula-phase requirements:

- ADP, rankings, mock drafts, big boards, auction values, projections, consensus, market values, and league rank cannot directly drive private football value.
- Market and projection data may be used only in context, sanity review, trade-liquidity, and audit comparison lanes.
- Source-limited combine/pro-day data cannot drive private football value until license/source status allows it.
- Missing evidence cannot become zero, average, or positive evidence.
- Review-only identity rows cannot feed formula-facing matrices.
- Silent fuzzy joins remain forbidden.
- Every formula-facing feature group needs source status, receipt pointers, and allowed model lane.
- Research reports inform formulas but are not feature rows.

## Required Sanity Fixtures For Formula Phases

### Elite RB Sanity

An elite RB candidate should clear at least two of:

- top-tier weighted opportunities per game
- top-tier snap/carry/touch share
- strong rushing or total first-down share
- strong goal-line or red-zone role
- credible route/target role
- age/workload profile still inside an acceptable window

Automatic review if:

- age 27+
- value depends on TD rate or YPC
- route/target role is weak
- recent lower-body or workload confidence is poor

### Elite WR Sanity

An elite WR candidate should clear:

- strong target share or TPRR
- strong routes/route participation
- strong YPRR or first downs per route
- meaningful receiving first-down share or yardage share
- age and offensive context not in sharp decline

Automatic review if elite value is mostly:

- TD spike
- yards per target
- catch rate
- small route sample
- vacated-target assumption
- market rank

### 1QB QB Sanity

A QB should not become a top dynasty asset in this league unless:

- projected VORP over QB replacement is large
- rushing production creates weekly ceiling
- job security is strong
- rushing-age decline is handled honestly

Automatic review if:

- QB is a QB7-QB12 style scorer with limited rushing
- QB outranks elite RB/WR without clear VORP receipts
- rushing QB age 29-31 is valued as if peak rushing is permanent

### No-Premium TE Sanity

A TE should only get a premium if:

- route participation is near full-time
- target share is meaningfully above replacement TE norms
- top-2 team target status is plausible or proven
- receiving first-down and yardage production create real VORP

Automatic review if value is based on:

- snap share without routes
- TD-only production
- size/athleticism without targets
- late-breakout hope
- TE scarcity borrowed from TE-premium formats

### Aging Veteran Sanity

Each veteran in caution or decline lanes must separate:

- skill indicators
- role indicators
- availability indicators
- market/liquidity indicators

Buy/hold signal:

- role stable
- sticky metrics stable
- TDs down or market depressed
- current-year private value above market cost

Sell/shop signal:

- routes/touches/targets/first-down share down
- efficiency down
- injury recurrence up
- market still name-driven

### Rookie And Prospect Sanity

Every rookie/prospect score must show:

- admitted identity
- draft capital lane
- position-specific production/share features
- age/lifecycle features
- source coverage
- missingness confidence cap
- market context excluded from private value

Required validation:

- beat draft-capital-only baseline before trust
- beat market-only baseline before trust
- use chronological or leave-one-class-out validation
- keep wide uncertainty bands for rookies

### Niners Roster Sanity

Because the user team is the Niners, future formula phases must include named roster sanity checks before decision use:

- Niners RBs must reflect role, age, first-down production, injury confidence, and roster-specific opportunity.
- Niners WRs must reflect target earning, route evidence, first-down production, and aging curve.
- Niners QB valuation must remain 1QB-adjusted and not overprice replaceable QB depth.
- Niners TE valuation must respect no TE premium and require route/target receipts.
- Any cut/trade recommendation for a Niners roster player must carry a player-level receipt and uncertainty warning.

## Formula-Phase Entry Criteria

Formula implementation may begin only after:

- Phase 10N evidence admission remains passing.
- Formula-facing matrices remain leakage-safe.
- Current review-only prospects remain quarantined or are explicitly admitted by a later identity phase.
- Source-limited evidence remains blocked from private value.
- The formula phase references this document as a requirements source.
- New formulas include tests for the sanity fixtures above.

## Locked Status

Phase 10O is complete when this document exists and static checks pass. It intentionally stops before formula code. The next phase may design or implement formulas, but it must prove that every formula satisfies this requirements lock rather than tuning to opinion or market consensus.
