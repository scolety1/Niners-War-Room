# Model v4 Position Formula Proposal

Created: 2026-05-16

This document proposes the review-only Model v4 position formula design before
any formula is coded. It does not change active rankings, player scores, app
readiness, or legacy outputs.

Authoritative context:

- `docs/model_v4/FORMULA_LANE_ARCHITECTURE.md`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.md`
- `docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`
- `docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.md`
- `docs/model_v4/LEAGUE_RULES_LOCK.md`

## Proposal Policy

These component mixes are starting proposals for the Phase 3C review-only config.
They are not final weights and they are not manual ranking overrides.

The proposal must be judged by:

- source-backed receipts
- sanity fixture dry runs
- named-player audits
- component contribution reconciliation
- no-blind-tuning review notes

Sanity fixtures define review expectations, not exact output rankings. If the
future model disagrees with a sanity belief, the correct next step is receipt
review and issue classification, not automatic weight forcing.

## Phase 6A Formula Patch Notes

Phase 6A applied only fixture-backed review-only formula changes after the
Phase 5 source-scope and missing-evidence repairs:

- QB `position_scarcity_suppression` is now emitted as an actual receipt
  component. The config already reserved 18% weight for it, but the calculator
  previously omitted the component.
- TE `no_premium_suppression` is now emitted as an actual receipt component.
  The config already reserved 10% weight for it, but the calculator previously
  omitted the component.
- WR projection weight increased because Phase 5G showed current raw-stat
  projection evidence was being overwhelmed by stale 2022-2024 production and
  usage evidence while route data remains unavailable.
- Established-veteran missing value evidence now gets a small uncertainty
  haircut after evidence-adjusted reweighting. Missing data is still not scored
  as zero production, but missing projection evidence no longer becomes a
  hidden ranking advantage.

All changes remain review-only and do not affect active app rankings.

## Phase 7B Focused Repair Notes

Phase 7B applied only issues confirmed by the external audit triage:

- Incoming rookies with missing production, first-down, usage, snap, projection,
  age, and young-prior evidence are capped at weak/review confidence until
  sourced rookie-board or prospect data exists.
- QB `position_scarcity_suppression` is now a small 1QB replacement guard and
  elite rushing-QB exception, not a large positive scarcity boost. Elite rushing
  QBs keep value through production, rushing, projection, and start-security
  receipts, while the 1QB lane prevents superflex-style inflation.
- The QB weight mix now gives `position_scarcity_suppression` the largest share
  of the QB lane so raw QB scoring volume cannot outrank core RB/WR assets by
  default in this 10-team, 1QB format.

All changes remain review-only and do not affect active app rankings.

## Shared Component Definitions

| Component | Meaning |
| --- | --- |
| Production | Recent LVE-scored NFL production using official rules, with no PPR and 0.4 first-down scoring. |
| First-down scoring fit | How well the player earns rushing/receiving first downs and TDs in this scoring format. |
| Usage/opportunity | Targets, carries, shares, weighted opportunities, red-zone use, and goal-line use. |
| Snap/proxy role | Offensive snap share as a role proxy. This is not route participation. |
| Projection | Raw-stat projections recomputed to exact LVE scoring, never supplied non-LVE points. |
| Age/dropoff | Position-specific age window, experience, fragility, and dynasty runway. |
| Injury/context | Injury and durability information as confidence/risk context, not a production booster. |
| Young-player prior | Lifecycle-limited draft/prospect prior blended with NFL evidence and decay. |
| Confidence | Trust language and penalties from source quality, identity, missing fields, and proxy-heavy evidence. |

## RB Proposal

### Goal

Value RBs for a 10-team, 1QB, non-PPR league where rushing/receiving first
downs matter and elite RB weekly advantage is meaningful, while still punishing
fragility, age cliffs, committee risk, and unsupported rookie-prior boosts.

### Proposed Dynasty Asset Components

| Component | Proposed Weight | Notes |
| --- | ---: | --- |
| production | 24 | Recent LVE points and durable scoring evidence. |
| first-down scoring fit | 14 | Rush/receiving first downs and TD fit. |
| usage/opportunity | 24 | Carries, RB target share, weighted opportunities, red-zone and goal-line work. |
| snap/proxy role | 8 | Role proxy only; lower weight because snaps are not route/share proof. |
| projection | 10 | Recomputed raw-stat projection with source-status penalty. |
| age/dropoff | 12 | RB age curve, workload fragility, and dynasty runway. |
| young-player prior | 8 | Applies only to young/incoming RBs; decays with NFL evidence. |
| injury/context confidence effect | confidence only | Lowers confidence/risk language; does not directly boost value. |

Total scoring weight: 100 before confidence language and review penalties.

### Formula Intent

- Elite young workhorse RBs should score strongly through production, usage, and
  first-down fit.
- Young RBs without NFL evidence can benefit from draft/prospect prior, but only
  enough to express uncertainty and upside.
- Older RBs can remain high if production and usage support it, but age/dropoff
  and injury context must be visible.
- Low-volume handcuffs or ambiguous rookies cannot outrank useful starters on
  draft capital alone.

### Expected Sanity Fixture Behavior

- Bijan and Gibbs should anchor the elite RB tier unless receipts reveal a major
  data issue.
- Achane should profile as core/elite unless role, injury, or confidence
  receipts explain a downgrade.
- McCaffrey can remain high, but age/dropoff and injury context must be visible.
- Kaleb Johnson must not jump useful established players on young prior alone.

### Formula Risks

- Overweighting usage could make fragile committee RBs look safer than they are.
- Underweighting age could leave older RBs too high for dynasty.
- Overweighting young prior could recreate the Kaleb Johnson problem.
- Projection gaps can distort RBs if baseline projections look like real
  forecasts.

## WR Proposal

### Goal

Value WRs through target earning, production stability, first-down fit, age
runway, and role security without using unavailable route metrics as fake
evidence.

### Proposed Dynasty Asset Components

| Component | Proposed Weight | Notes |
| --- | ---: | --- |
| production | 22 | Recent LVE-scored production and stability; lower than Phase 3 because current production source is stale relative to 2026 projection context. |
| first-down scoring fit | 12 | Receiving first downs and TD conversion. |
| usage/opportunity | 20 | Targets, target share, red-zone targets, weighted opportunity. |
| snap/proxy role | 5 | Role proxy only; not routes run or route participation. |
| projection | 19 | Recomputed projection with clear source status; stronger in Phase 6A because it is current raw-stat evidence while route data is unavailable. |
| age/dropoff | 12 | WR prime, late-prime, and age decline windows. |
| young-player prior | 10 | Stronger than RB for early-career WR patience, but still evidence-decayed. |
| injury/context confidence effect | confidence only | Lowers confidence/risk language; does not directly boost value. |

Total scoring weight: 100 before confidence language and review penalties.

### Formula Intent

- Elite target earners should remain high even in a non-PPR format because
  targets drive yards, TD chances, and first downs.
- Young WRs with real NFL evidence should beat year-one prospects unless the
  prospect prior and projection evidence are unusually strong.
- Aging WRs can stay useful, but must not quietly outrank young cornerstone RBs
  without overwhelming production and role receipts.
- Missing route data should be a visible confidence limitation, not a neutral
  score that props up or buries players.

### Expected Sanity Fixture Behavior

- JSN, Puka, Chase, Jefferson, Amon-Ra, Lamb, and Nabers should live in the
  broad core/elite WR area unless receipts explain otherwise.
- JSN below Tee Higgins is a review finding requiring target, production, age,
  and confidence receipts.
- BTJ should usually beat Luther Burden until Luther has NFL evidence, unless
  receipts show a source-backed exception.
- Keenan Allen and similar aging WRs should not beat young cornerstone RBs
  without obvious receipt-backed justification.

### Formula Risks

- Missing route metrics can hide WR role uncertainty.
- Overweighting production can overvalue aging WRs.
- Overweighting young prior can overvalue prospects before NFL evidence.
- Underweighting target earning can miss true WR breakouts.

## QB Proposal

### Goal

Suppress replaceable QBs in a 10-team 1QB league while still recognizing true
difference-makers, especially rushing QBs with durable start security.

### Proposed Dynasty Asset Components

| Component | Proposed Weight | Notes |
| --- | ---: | --- |
| production | 18 | Recent LVE passing/rushing scoring. |
| first-down scoring fit | 6 | Mostly rushing first downs and rushing TD fit. |
| usage/opportunity | 10 | Starts, designed rushes, pass volume, team role. |
| snap/proxy role | 4 | Start security proxy, not a major value driver. |
| projection | 10 | Recomputed passing/rushing projection. |
| age/dropoff | 7 | Passing runway plus rushing-age decline. |
| position scarcity suppression | 41 | 1QB replacement suppression and elite exception gate. |
| young-player prior | 4 | Applies only to eligible young QBs; must decay with starts/NFL evidence. |
| injury/context confidence effect | confidence only | Start security and injury risk affect trust language. |

Total scoring weight: 100 before confidence language and review penalties.

### Formula Intent

- Elite difference-maker QBs can remain valuable, but not ahead of elite RB/WR
  assets by default.
- Replaceable starting QBs should be pushed down by the 1QB replacement
  suppression component.
- Rushing production matters, but rushing-age decline and start security must be
  visible.
- Daniel Jones / Brock Purdy / Joe Burrow-style controls should separate
  replaceability, stability, and ceiling rather than being lumped together.

### Expected Sanity Fixture Behavior

- Josh Allen, Jalen Hurts, Lamar Jackson, and similar rushing/elite QBs can be
  exceptions with receipts.
- Replaceable QBs should not crowd out elite RBs or WRs.
- Daniel Jones should not be treated like a cornerstone dynasty asset without a
  very strong receipt-backed reason.

### Formula Risks

- Too much 1QB suppression can bury genuine weekly edge.
- Too little suppression recreates superflex-style QB inflation.
- Rushing-heavy QBs need age/injury context so rushing value is not treated as
  permanent.
- Projection-heavy QB scoring can overvalue one-year starter assumptions.

## TE Proposal

### Goal

Suppress ordinary TEs in a no-TE-premium format while preserving true elite
volume exceptions.

### Proposed Dynasty Asset Components

| Component | Proposed Weight | Notes |
| --- | ---: | --- |
| production | 22 | Recent LVE receiving production. |
| first-down scoring fit | 10 | Receiving first downs and TD role. |
| usage/opportunity | 24 | Targets, target share, red-zone targets, weighted opportunity. |
| snap/proxy role | 8 | Role proxy only; routes are unavailable. |
| projection | 10 | Recomputed receiving projection. |
| age/dropoff | 10 | TE late-prime and age cliff handling. |
| no-premium suppression | 10 | Suppresses replaceable TEs relative to RB/WR. |
| young-player prior | 6 | Applies to young TEs, but no-premium and missing evidence remain visible. |
| injury/context confidence effect | confidence only | Lowers confidence/risk language. |

Total scoring weight: 100 before confidence language and review penalties.

### Formula Intent

- Brock Bowers, Trey McBride, and Sam LaPorta can be elite exceptions only if
  target/production receipts justify it.
- Replaceable TEs must be suppressed because there is no TE premium.
- Older TEs need age/dropoff visibility.
- Young TEs with prospect prior but little NFL evidence should remain review
  unless production or projection support them.

### Expected Sanity Fixture Behavior

- Elite TEs can remain valuable but must show volume evidence.
- No-premium suppression should keep ordinary TEs from passing useful RB/WR
  assets.
- Oronde Gadsden II and similar year-one TEs should show young-prior and missing
  NFL evidence clearly.

### Formula Risks

- Too much TE suppression can miss rare elite exceptions.
- Too little suppression can overvalue replaceable TEs in no-premium.
- Missing route data is especially important for TE role evaluation.
- Young TE priors are volatile and should not fake production.

## Cross-Position Logic

### 10-Team 1QB Suppression

The QB formula needs a replacement/value gate after raw QB scoring. The gate
should:

- suppress replaceable starters
- preserve elite/rushing weekly-difference makers
- show start security and rushing-age risk in receipts
- prevent QB scoring volume from behaving like superflex value

This is not a flat QB penalty. It is a scarcity adjustment based on this league
format.

### No-TE-Premium Suppression

The TE formula needs a no-premium gate after volume and production components.
The gate should:

- suppress ordinary or replaceable TEs
- preserve true elite target-volume exceptions
- show target earning and role evidence
- flag missing route/participation data as a confidence issue

### RB Fragility And Workload Risk

RBs should receive strong value from real workload and first-down scoring fit,
but the model must show:

- workload concentration
- receiving role
- goal-line usage
- age/dropoff window
- injury/context confidence effects
- committee or small-sample volatility

This is the key guardrail against making every high-touch RB look equally safe.

### WR Target Earning And Stability

WRs should emphasize target earning and production stability because targets
drive yards, TD chances, and first downs even without PPR. The model must show:

- target share
- receiving first-down fit
- production stability
- red-zone target context
- age/dropoff
- route data unavailable warning

This is the key guardrail against burying elite WRs behind ordinary RB volume.

### Young-Player Bridge Decay

Young-player prior should:

- be strongest for incoming rookies and year-one players with little NFL data
- decay after year one
- shrink further after year two
- become tiny after year three
- be removed for established veterans
- decay faster when real NFL production and role evidence are strong
- remain visible as a separate receipt section

Draft capital explains uncertainty and upside. It does not fake NFL production.

## Expected Sanity Fixture Behavior

These are expected review directions, not exact final rankings:

- Bijan and Gibbs should anchor the elite RB tier.
- Achane should read as core/elite unless injury or role receipts explain a
  downgrade.
- McCaffrey can remain high, but age/dropoff must be visible.
- JSN, Puka, Chase, Jefferson, Amon-Ra, Lamb, and Nabers should remain in the
  broad core/elite WR area unless receipts explain otherwise.
- JSN below Tee Higgins is a review finding, not an automatic formula failure.
- BTJ should generally rank above Luther Burden until Luther has NFL evidence.
- Kaleb Johnson should not outrank useful established veterans on prior alone.
- Replaceable QBs should not crowd out elite RB/WR assets.
- Ordinary TEs should be suppressed in no-premium.
- Market and league rank must not move private football value.

## Formula Risks Before Implementation

| Risk | Why It Matters | Mitigation |
| --- | --- | --- |
| RB volume overcorrection | Could put ordinary/high-touch RBs above elite WRs. | Require age, role, receiving, and confidence receipts; test RB/WR fixtures. |
| WR route-data gap | Free data lacks true routes, TPRR, and YPRR. | Keep route unavailable visible and use target/share/snap proxy carefully. |
| Young prior overreach | Could inflate rookies or early-career players without NFL evidence. | Keep young prior separate, decayed, and capped by confidence. |
| Aging veteran overvaluation | Production-only models can overrate declining veterans. | Make age/dropoff and injury/context visible and meaningful. |
| QB inflation | Raw QB points can look too valuable in 1QB. | Apply 1QB replacement suppression and elite exception gate. |
| TE inflation | Generic dynasty TE value can leak into no-premium format. | Apply no-premium suppression and volume exception logic. |
| Projection false certainty | Local baseline or incomplete projections can fake confidence. | Keep projection source status visible and penalized. |
| Market contamination | Market value can accidentally become private value. | Keep market out of Dynasty Asset Value and test isolation. |
| League-rank contamination | League rank can accidentally become player quality. | Keep league rank in roster-rule context only and test isolation. |
| Hidden defaults | Neutral values can look like real evidence. | Receipt contract must show unavailable/imputed sections. |

## Phase 3B Exit Criteria

Phase 3B is complete when:

- RB, WR, QB, and TE proposed component mixes are documented.
- Cross-position logic is documented.
- Sanity fixture expectations are described without forcing exact rankings.
- Formula risks are listed before implementation.
- No formula code is written.
- Active rankings remain untouched.
