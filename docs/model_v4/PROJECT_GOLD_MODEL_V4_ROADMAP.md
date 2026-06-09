# Project Gold Model v4 Roadmap

Model v4 is the clean rebuild after the v3 Truth Set Lab work proved the same
thing repeatedly: the legacy scoring brain can be audited, patched, and made
safer, but it cannot be trusted as the final decision engine.

This roadmap is the persistent plan and stakes record for the rebuild.

## Current Status Update: RotoWire Evidence Spine

Date: 2026-05-17

- RotoWire manual exports have been archived and indexed as the primary local
  licensed evidence package.
- Historical player stats, snap/target/alignment/route role data, depth charts,
  injuries, team context, projections, rankings context, ADP, and combine/workout
  rows now have clean intake outputs.
- RotoWire truth-set identity coverage is 80 / 80.
- RotoWire evidence coverage is 75 covered / 5 review; the review players are
  incoming rookies without NFL production or role history.
- A review-only RotoWire stats-first value layer exists. It does not use
  projections, market, or league rank for private value.
- Review-only replacement/VORP rows exist for the 10-team, 1QB, non-PPR
  structure. They are now rushing/receiving-first-down-aware, using
  `estimated_from_history` first-down estimates from source-safe 2022-2024
  nflverse first-down history when direct 2025 fields are unavailable.
- A review-only RotoWire dynasty candidate layer exists with component receipts,
  age/dropoff caps, confidence caps, named-player review, and sanity review.
- The RotoWire candidate layer is not decision-ready; it still needs
  rookie/prospect evidence, focused WR/RB receipt review, first-down estimation
  audit, and external audit before app promotion.

## Stakes

- The league is a $1,000 dynasty league.
- The official drop / Roster Declaration Day is June 15.
- Earlier trade guidance is valuable, but false certainty is worse than waiting.
- The model must become usable before June 15 so trades can be explored before
  the declaration deadline.
- The model must be accurate enough to explain roster decisions with evidence,
  not mystery scores.
- If Model v4 cannot prove a decision is ready, it must say so clearly.

## Core Decision

Stop trying to rescue the legacy scoring brain. Reuse infrastructure where it
has been proven useful, but build a clean `model_v4` decision lane.

Reuse where safe:

- data-pack ingestion shape
- Sleeper roster and league-rank imports
- official league rules extraction
- identity bridge pieces that pass audit
- audit packet exports
- receipt display patterns after they are tied to v4 scores
- draft board state/UI if separated from scoring truth

Do not reuse as trusted logic:

- legacy scoring formulas
- legacy action labels like `core hold`, `bubble`, and `shop` without v4-defined
  thresholds
- hidden neutral defaults counted as evidence
- market data inside private football value
- route metrics unless legally structured and source-safe
- old readiness gates that pass because the UI is quiet

## Required V4 Outputs

Model v4 must answer separate questions with separate outputs.

1. Dynasty Asset Value
   - Pure football/dynasty value for this league format.
   - No roster-rule mechanics.
   - No trade-market contamination.

2. Roster Decision Value
   - My-roster decision layer for keep, review, shop, release, and forced-release
     analysis.
   - Built from Dynasty Asset Value plus roster context and confidence.

3. Required Top-Five Release Analysis
   - Operates only on the Roster's League-Rank Top Five.
   - Explains the least painful required release slot.
   - Keeps non-top-five drops as secondary context only.

4. Trade Context
   - Shows market/liquidity and model-vs-market disagreement.
   - Never changes private football value.
   - Trade posture should be aggressive but smart: find exploitable market
     imbalance, but preserve strong assets when the edge is not real.

5. Draft Value
   - Available-player-only board for the offline mixed rookie/veteran draft.
   - Separate from rostered-player keeper decisions.

6. Confidence
   - Controls how strongly the app is allowed to speak.
   - Low confidence creates review language, not hidden burying.

## Sprint 0: Freeze, Rules Lock, And Spec

- Freeze legacy rankings as audit-only.
- Lock the rulebook in `docs/model_v4/LEAGUE_RULES_LOCK.md`.
- Create a v4 model spec before formula work.
- Confirm scoring constants in tests, especially:
  - no PPR
  - no TE premium
  - interceptions are -1
  - fumbles lost are -1
  - rushing/receiving first downs are 0.4
- Confirm the app cannot show decision-ready labels from legacy logic.

Exit condition:

- Rules and stakes are documented.
- Legacy model is not allowed to declare readiness.
- V4 work has its own lane.

## Sprint 1: Evidence Spine

- Define source statuses:
  - imported real data
  - derived real data
  - proxy evidence
  - estimated
  - context only
  - unavailable
  - rejected
- Promote only safe structured data:
  - nflverse production
  - rushing/receiving first downs
  - play-by-play derived target/carry/red-zone/goal-line usage
  - snap share
  - recomputed LVE projections with source labels
- Keep restricted or weak data out:
  - manually compiled player stat tables
  - unsourced injury health claims
  - true route metrics without licensed structured source
  - market data in private value

Exit condition:

- Every feature row knows its source status.
- Hidden defaults cannot pretend to be data.
- Rejected sources cannot enter v4 scoring.

## Sprint 2: Truth Set And Sanity Fixtures

- Build a small truth set before formulas.
- Use `docs/model_v4/FOOTBALL_SANITY_BELIEFS.md` as the initial sanity-belief
  source.
- Include:
  - every Niners roster decision player
  - elite RBs
  - elite WRs
  - young bridge assets
  - QB controls
  - TE controls
  - older decline-risk players
  - obvious cuts
- Convert football beliefs into testable fixtures.
- Require every surprising order to have receipts.

Exit condition:

- We have fixtures that catch the failures that broke trust in the legacy model.
- We know which rankings are data problems and which are formula problems.

## Sprint 3: Position Models

- Rebuild positions independently.
- RB:
  - production
  - opportunity
  - first-down/TD fit
  - age/workload fragility
  - injury context
  - dynasty window
- WR:
  - target earning
  - production stability
  - first-down/TD fit
  - age curve
  - role security
- QB:
  - 1QB replacement suppression
  - elite exception
  - rushing value only when paired with start security
- TE:
  - no-premium suppression
  - route/target gate where data exists
  - elite exception

Exit condition:

- Position scores reconcile through receipts.
- Position sanity tests pass before cross-position sorting.

## Sprint 4: Cross-Position Calibration

- Put position outputs onto one LVE dynasty board.
- Calibrate against lineup demand:
  - 3 WR
  - 2 RB
  - 2 flex
  - 1 QB
  - 1 TE
  - no TE premium
- Test:
  - elite RB versus elite WR
  - fragile RB versus stable WR
  - young bridge player versus proven player
  - QB/TE suppression

Exit condition:

- Cross-position ranks are explainable.
- No single feature can create absurd overall rankings by itself.

## Sprint 5: Roster Decision Layer

- Rebuild My Team from v4 values.
- First usable roster output must include:
  - safest 23 keepers
  - required top-five release decision
  - trade/shop list before drop date
- Replace confusing labels with:
  - clear hold
  - likely hold
  - review
  - shop
  - release candidate
  - required top-five release candidate
- Build the forced-release decision from the Roster's League-Rank Top Five only.
- Make the receipts readable before UI polish.

Exit condition:

- The user can inspect pre-declaration roster decisions without relying on the
  draftable pool being final.

## Sprint 6: Trade And Draft Layers

- Rebuild Trade Lab after private value is credible.
- Keep trade-market value separate from model value.
- Rebuild draft surfaces using the real draftable pool:
  - rookies
  - official released veterans
  - legal free agents
  - manual review adds
- Keep draft readiness blocked until official release data is available.

Exit condition:

- Trade and draft pages use credible v4 values, not legacy score leftovers.

## Sprint 7: External Audit And Readiness Gate

- Export a neutral audit packet.
- Run external/pro audit without leading examples.
- Patch only verified issues:
  - source bug
  - identity bug
  - normalization bug
  - formula bug
  - label/action threshold bug
- Mark only the gate that truly passes:
  - roster decisions
  - draft readiness
  - final money decisions

Exit condition:

- If roster decisions are ready before June 15, the app says so.
- If not, the app gives the exact blocker instead of pretending.

## Non-Negotiable Guardrails

- No final-ready label from legacy logic.
- The user does not need to inspect legacy model pages during the rebuild; hide
  or block legacy action labels until v4 defines them cleanly.
- No market data in private/model value.
- No hidden neutral defaults as imported evidence.
- No route data unless source-safe.
- No player-specific patch unless the general rule is correct.
- No formula tuning without fixtures and receipts.
- No UI polish in place of model truth.
- No draft-ready label before the real draftable pool is loaded.

## Confirmed User Inputs

- Official team name: Niners.
- Official drop date: June 15.
- Kicker treatment: ignore for player value; use only for roster mechanics if
  necessary.
- Draft picks: assume Sleeper pick ownership is correct unless later export
  says otherwise.
- Desired roster decision output: safest 23, required top-five release, and
  aggressive-smart trade/shop list.
- Sanity beliefs: review-only guardrails. The model may disagree, but must prove
  why with receipts and source evidence.
- Data source trust order:
  1. official league files/rules
  2. Sleeper roster/player IDs
  3. nflverse structured data
  4. paid structured/API data if licensed
  5. agent research only as review evidence, never direct scoring

## Immediate Next Step

Start with:

`Project Gold Model v4 / Sprint 0: Freeze, Rules Lock, And Spec`

Do not start formula rebuild work until Sprint 0 and the v4 feature/source
contract are complete.
