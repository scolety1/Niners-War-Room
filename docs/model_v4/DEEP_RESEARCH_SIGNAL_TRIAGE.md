# Deep Research Signal Triage

Date: 2026-05-17

## Inputs Reviewed

Archived reports:

- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-26-audit-framework.md`
- `local_exports/model_v4/raw_user_exports/deep_research/deep-research-report-27-rookie-signals.md`

Inline user-provided report:

- Position-by-position dynasty signal hierarchy for a 10-team, 1QB, non-PPR
  league with rushing/receiving first-down scoring.

The third Deep Research response was provided inline because it could not be
exported as markdown. No additional Deep Research report is currently required
before the next implementation patch.

Machine-readable triage:

- `docs/model_v4/DEEP_RESEARCH_SIGNAL_TRIAGE.csv`

## Verdict

The research supports the current rebuild direction:

- build from historical stats and usage first
- use first-down scoring directly
- value players above replacement, not by raw points
- suppress QB and TE value for this 10-team, 1QB, no-TE-premium league
- keep market, ADP, and rankings as sanity/context only
- keep projections bounded and separate from core value
- cap confidence when evidence is missing
- build a separate rookie/prospect layer instead of pretending incoming rookies
  have NFL production evidence

It also changes one important source assumption: your licensed RotoWire exports
make routes run, TPRR, YPRR, target share, snap counts, target leaders, receiver
alignment, and TE route data usable as controlled local evidence. Direct route
participation still needs careful handling unless it is explicitly exported or
derived from a valid denominator.

## Research-Backed Priorities

### 1. Replace Raw Value With League-Adjusted VORP

The model should not finalize Dynasty Asset Value from raw evidence percentiles.
It needs a replacement baseline for this exact league shape.

Action:

- add a VORP/replacement layer before app promotion
- compute position baselines for 10-team, 1QB, non-PPR, first-down scoring
- keep QB/TE suppressed unless they create a real replacement gap

### 2. Make First Downs Central

The reports agree that rushing/receiving first downs are not side details in
this format. They should remain first-class evidence.

Action:

- preserve `first_down_scoring_fit`
- prefer direct rushing/receiving first-down fields where available
- keep estimated first-down projections labeled and penalized

### 3. RB Formula Needs Role, First Downs, Age, And Fragility

RBs should be short-window, role-driven assets. Volume and high-value touches
matter more than raw efficiency.

Action:

- emphasize weighted opportunities, target role, first-down share, red-zone,
  and goal-line role
- add sharper age/dropoff and workload-fragility logic
- shrink yards-per-carry and explosive efficiency unless volume supports it

### 4. WR Formula Needs Target Earning And Route Evidence

WR value should be built around target earning, route volume, YPRR, air yards,
first-down production, and age/stability.

Action:

- promote licensed RotoWire routes run, TPRR, YPRR, team target share, and air
  yards share into controlled WR evidence
- audit elite WRs again after route evidence is wired in
- do not rely on TD spikes, catch rate, or raw yards per target alone

### 5. QB Formula Needs Replacement Math

In 1QB, even accurate QB production can still be replaceable. Rushing QBs can
matter, but only when they create a meaningful VORP edge.

Action:

- keep elite rushing-QB exception
- add replacement baseline instead of raw QB percentile value
- ensure non-rushing QB6-QB12 profiles cannot climb over core RB/WR assets

### 6. TE Formula Needs A Receiving-Engine Filter

No-TE-premium means ordinary TE production should be replaceable. The TE must
earn routes and targets like a real receiver before receiving a premium.

Action:

- use TE route data and target evidence
- keep no-premium suppression
- require VORP gap before TE gets elite cross-position treatment

### 7. Rookie Layer Must Be Separate

The rookie report strongly supports draft capital as the starting prior, but
also requires age-adjusted college production, market share, route/efficiency,
athletic testing, injury modifiers, landing spot, and confidence caps.

Action:

- wait for files in `rookie_manual/incoming`
- do not invent college or athletic values
- cap confidence until sourced rookie data exists
- decay draft capital after NFL evidence arrives:
  - rookie preseason: 100%
  - after Year 1: about 45%
  - after Year 2: about 20%
  - after Year 3: about 5%

### 8. Promotion Needs An Audit Gate

The audit-framework report is clear: app promotion should require manifests,
leakage checks, ablation checks, fixtures, calibration, and player receipts.

Action:

- build a RotoWire audit packet before promoting to app surfaces
- include ablations showing projections and market do not drive private value
- include named-player receipts and fixture outcomes

## Immediate Patch Sequence

1. Update the v4 source contract for licensed RotoWire route evidence.
2. Build a RotoWire-powered dynasty candidate layer on top of stats-first value.
3. Add VORP/replacement baselines by position.
4. Add age/dropoff and RB fragility adjustments.
5. Add WR route/target earning evidence and re-run elite WR audit.
6. Add rookie/prospect intake once user uploads rookie files.
7. Re-run sanity fixtures.
8. Produce external audit packet before app promotion.

## Guardrails

- Do not use ADP, market, or rankings as private value.
- Do not let projections drive core value.
- Do not treat missing data as zero.
- Do not treat injury absence as healthy evidence.
- Do not give incoming rookies strong confidence without sourced rookie data.
- Do not promote to My Team or War Board before fixtures and audit pass.
