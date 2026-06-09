# Project Gold Model v2 Roadmap

> Superseded: this roadmap has been replaced by
> `docs/model_v4/PROJECT_GOLD_MODEL_V4_ROADMAP.md`. Do not start new work from
> this v2 plan.

## Stakes

This rebuild exists because the legacy model became too hard to trust. The project
has been circling through patch, audit, retune, and UI cleanup without producing a
ranking system that feels safe for a $1,000 dynasty league.

The standard for Model v2 is higher:

- It must be usable before the June 15 drop date.
- It should become useful earlier if possible, so trade decisions can happen before
  forced releases.
- It must never call rankings, roster decisions, draft decisions, or final money
  decisions ready unless the relevant gates actually pass.
- It must explain surprising rankings with receipts, source quality, and tests.
- It must separate football value from roster-rule mechanics and trade-market context.
- It must not hide weak data behind confident labels.

If the model cannot meet this standard, the correct answer is to say so clearly
instead of dressing uncertainty up as a finished tool.

## Core Decision

Stop trying to rescue the legacy scoring brain. Keep useful infrastructure, but
build a clean `model_v2` lane beside it.

Reuse where safe:

- data-pack imports
- Sleeper roster/rank inputs
- identity bridge pieces that pass audit
- receipt/export machinery
- draft board UI/state where separate from scoring
- My Team page shell after labels are honest

Do not reuse as trusted logic:

- legacy scoring formulas
- legacy action thresholds
- legacy readiness assumptions
- legacy "Core Hold" / "Bubble" labels without v2 confidence gates
- hidden neutral defaults as real evidence

## Required Model Outputs

Model v2 must produce separate outputs for separate questions:

1. Dynasty Asset Value
   - Pure player value for this league format.
   - No roster-rule, forced-release, or market contamination.

2. Roster Decision Value
   - Keep, review, shop, cut-risk, and forced-release decisions for my roster.
   - Built on top of Dynasty Asset Value plus roster context.

3. Trade Context
   - Market/liquidity and model-vs-market edge.
   - Never allowed to change private football value.

4. Draft Value
   - Available-player-only value for the mixed rookie/veteran draft.
   - Separate from rostered-player keeper decisions.

5. Confidence
   - Controls how strongly the app is allowed to speak.
   - Low confidence must reduce action certainty, not silently bury players.

## Rebuild Phases

### Sprint 0: Legacy Freeze And v2 Spec

- Freeze current model as legacy audit-only.
- Write the v2 model spec.
- Identify reusable services and forbidden legacy logic.
- Keep all current outputs review-only.

### Sprint 1: League Rules And Data Contract

- Lock one canonical league-rules source.
- Define scoring and roster mechanics.
- Define required, helpful, optional, unavailable, paid-candidate, and research-only inputs.
- Ban unverifiable agent data from scoring.

### Sprint 2: Truth Set And Sanity Fixtures

- Build a truth set before formulas.
- Include my roster, elite RBs, elite WRs, young bridge assets, QB/TE controls,
  older vets, and obvious cuts.
- Convert football sanity beliefs into regression tests.
- Include cross-position fixtures that catch Achane/BTJ/Keenan/Kaleb-style failures.

### Sprint 3: Position Models

- Rebuild RB, WR, QB, and TE separately.
- RB: age, injury, workload fragility, first-down/TD fit, dynasty window.
- WR: target earning, production stability, role, age, efficiency.
- QB: 1QB replacement suppression, rushing/start-security exceptions.
- TE: no-premium suppression, route/target gate, elite exception.

### Sprint 4: Cross-Position Calibration

- Put positions onto one LVE dynasty board.
- Test elite young RBs versus uncertain young WRs.
- Test stable WRs versus fragile RBs.
- Test QB/TE suppression.
- Require every major surprise to have receipt support.

### Sprint 5: Roster Decision Layer

- Build My Team decisions from v2 values.
- Separate:
  - obvious hold
  - likely hold
  - needs data review
  - bubble/close call
  - shop
  - cut/stash
  - forced-release candidate
- Forced-release logic must operate on the roster's league-rank top-five group only.

### Sprint 6: Trade And Draft Layers

- Add trade context without contaminating private value.
- Reconnect Rankings and Draft Board only after draftable pool is real.
- Keep released veterans as a later draft-room input, not a blocker for pre-drop roster review.

### Sprint 7: External Audit And Final Gate

- Export neutral audit packet.
- Run Pro/external audit.
- Patch only confirmed data, identity, normalization, formula, or label bugs.
- Mark only the gates that truly pass:
  - roster decisions
  - draft readiness
  - final money decisions

## Non-Negotiable Guardrails

- No green "ready" labels from legacy logic.
- No hidden defaults counted as real evidence.
- No market data in private/model value.
- No route metrics unless legally structured and source-safe.
- No formula tuning to match vibes without fixtures and receipts.
- No UI polish in place of model truth.
- No player-specific patching unless the general rule is also correct.
- No final decision-ready state until independent audit and gates pass.

## Near-Term Success Criteria

Before June 15, Model v2 should be able to answer:

- Who is my required top-five release candidate?
- Which players are obvious holds?
- Which players are true review rows?
- Which players should I actively shop?
- Which model disagreements are data problems versus real edge?
- Which trades should I explore before release declarations?

## Current Next Step

Start with:

`Project Gold Model v2 / Sprint 0: Legacy Freeze and Model Rebuild Spec`

Do not begin formula work until Sprint 0, rules lock, data contract, and sanity
fixture scaffolding exist.
