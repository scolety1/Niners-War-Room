# Niners War Room — Full Product Audit & Completion Plan V1

**Status:** Canonical planning document  
**Date:** 2026-08-17  
**Purpose:** Prevent scope drift while NWR moves from a collection of validated local capabilities into a complete, owner-usable Dynasty + Redraft product.

---

## 1. North Star

Niners War Room should become a complete fantasy-football decision system that uses:

1. **NWR's own models and governed evidence** where they are strongest.
2. **Existing NWR capabilities first** before building replacements.
3. **External open-source repositories, APIs, and public data** only where they provide a better component, pattern, interface, or missing capability.
4. **Active-league context** so every recommendation reflects the actual league being used.
5. **Clear authority labels** so NWR never disguises research, market consensus, external rankings, or missing data as a production NWR model.

The goal is **not** to bolt on random fantasy tools.

The goal is to audit everything we already have, audit the best external implementations, then deliberately assemble the strongest possible final NWR product.

---

# 2. Current Product Identity

## Niners War Room

This remains the overall software/product brand.

### Dynasty app
Primary original league context:
- Sleeper league: **Las Vegas Enginerds**
- Original team identity: **Niners**
- League ID previously recovered: `1344772855908290560`
- Dynasty remains its own product/workspace.

### Redraft app
Supports multiple isolated Redraft league workspaces.

Current real Redraft league:
- **Fantasy Gamers**
- Sleeper League ID: `1312983576827920384`
- Sleeper username: `scolety`
- 2026
- 10 teams
- PPR
- 1QB
- 15-round snake
- 1 QB / 2 RB / 2 WR / 1 TE / 1 FLEX / 1 K / 1 DEF / 6 bench

Installed Redraft currently also preserves an unidentified legacy profile:
- `10-team 1QB Standard`
- Do not assume or rename it to Niners without provenance.

---

# 3. Current Major NWR Assets That Must Be Audited Before Anything New Is Built

The next phase must inventory and classify the real current implementation of every item below.

## Dynasty analytical authorities
- Finished V1 veteran production authority
- Outcome V3
- Rookie Review
- 80-player Rookie Review refresh candidate
- Unified Research Preview
- Rookie ↔ Veteran multi-authority bridge
- Player Compare
- Player Detail
- Trade Decision Assistant
- Market context
- lifecycle / age / availability
- current owner watchlist / disagreement framework

## Redraft analytical authorities
- Redraft Champion
- combined veteran + rookie Redraft board
- league-specific scoring profiles
- replacement/VBD-style context
- low / projected / high projection evidence
- confidence / uncertainty
- Practical Mock support
- multi-league workspace
- Sleeper profile import
- read-only Sleeper pick reader
- manual K/DST support
- optional FantasyPros K/DST provider boundary
- Weekly Tools / K-DST streamer boundary

## Existing market / ADP-style assets to locate mechanically
Search the repository and artifacts for all existing fields/services involving:
- `market`
- `market_value`
- `market_rank`
- `market_gap`
- `dp_value`
- `dp_rank`
- DynastyProcess context
- Sleeper ADP
- platform ADP
- consensus ADP
- mock ADP
- draft position
- expected pick
- historical draft position
- replacement/VBD
- scarcity
- tiers
- tier gaps
- price / value overlays

**Do not assume these are absent.**
A major goal of the next audit is to determine whether Beat ADP, CPU mock behavior, and Market tools can be built mostly from existing NWR data.

---

# 4. Mandatory Process Rule

Before implementing any major new feature:

## Step A — Audit NWR
Classify each relevant existing capability as:
- `NWR_ALREADY_BETTER`
- `NWR_EXISTS_AND_CURRENT`
- `NWR_EXISTS_BUT_DISCONNECTED`
- `NWR_EXISTS_BUT_NEEDS_UPGRADE`
- `NWR_EXISTS_BUT_WRONG_AUTHORITY`
- `NWR_PARTIAL`
- `NWR_ABSENT`

## Step B — Audit external repositories / APIs
For each external candidate record:
- repository / provider
- exact commit/version inspected
- license
- freshness
- data/provider dependencies
- feature set
- architecture
- useful components
- integration cost
- privacy/safety implications
- whether it duplicates NWR
- whether it improves NWR materially

Classify:
- `COPY_WITH_ATTRIBUTION`
- `ADAPT_PATTERN`
- `CONCEPT_ONLY`
- `DATA_SOURCE_CANDIDATE`
- `API_CANDIDATE`
- `REJECT`

## Step C — Produce an adoption map
For every final NWR feature choose one:
- keep current NWR implementation
- reconnect existing NWR implementation
- upgrade existing NWR implementation
- adopt external component/pattern
- build missing capability
- defer

## Step D — Only then implement.

---

# 5. High-Priority External Repository Families Already Discovered

These are candidates for full inspection, not automatic adoption.

## Draft room / mock draft / draft assistant
- `zacharykirby/ai-nfl-fantasy-draft`
- `joewlos/fantasy_football_monte_carlo_draft_simulator`
- `justinmck/fantasy-football-draft-toolkit`
- `GambitAcid/NFL-Fantasy-AI-Draft-Predictor`
- `Remaerd369/draftcaster-simulator`
- `athibault-cyber/fantasy-football-draft-simulator-public`
- `zdybak/OverDraft`
- `thebutcher-board/the-board`
- `ParashDev/nfl-fantasy-draft-analyzer`
- `itsreverence/sleeper-draft-assistant`
- `Zeekeey-jpeg/Sleeper_Draft_Buddy`
- `awguzman/Sleeper-Draft-Agent`
- `windleypratt/sleeper-drafts`
- `kevsilve/sleeper-draft-viewer`
- `SleeperPy/SleeperDraftOrderFetcher`

### Key concepts to evaluate
- real snake draft board
- team columns / round rows
- recent picks
- complete draft log
- all-team rosters
- owner draft-slot selection
- CPU/bot picks
- undo/recovery
- autosave
- position runs
- tier cliffs
- next-pick availability
- "will this player make it back?"
- roster-aware recommendations
- deterministic vs stochastic opponent behavior
- live Sleeper draft synchronization

---

# 6. ADP / Beat ADP / Market Timing

This is a priority feature.

Candidate repositories:
- `VTNoble/adp-vs-projection`
- `MarkCirineo/ff-adp-compare`
- `najibismail95/Fantasy-Football-ADP-Comparison-Tool`
- `ball-and-chain-gfl/adp-board-2026`
- `lucas-huynh/fantasy_adp_projection_2026`
- `nirajvora/fantasy-football-adp-sync`
- `longtran3/FF_ADP`

Potential additional external providers should be evaluated only after existing NWR/Sleeper market data is inventoried.

## Desired owner-facing draft information
For each player:
- NWR Redraft rank
- position rank
- current ADP / expected pick
- expected round
- ADP source
- source freshness
- NWR minus market difference
- projected chance to survive to next owner pick
- roster fit
- positional cliff context

## Two concepts must remain separate

### NWR View
How much NWR likes the player relative to market.

Potential labels:
- `STRONG VALUE`
- `VALUE`
- `ALIGNED`
- `FADE`
- `STRONG FADE`

### Draft Timing
Whether to select now or wait.

Potential labels:
- `TAKE NOW`
- `VALID`
- `REACH`
- `WAIT`
- `LIKELY TO MAKE IT BACK`
- `UNLIKELY TO MAKE IT BACK`

Do not collapse player quality and market timing into one label.

## Beat ADP Pool
Create a dedicated owner tool showing players NWR values materially above market.

Possible columns:
- Player
- Pos
- NWR Rank
- ADP
- Expected Pick
- NWR Edge
- Make-It-Back %
- Current Round
- Recommendation
- Tier / positional cliff

---

# 7. Draft Room — Required Final Experience

The current mock is visually promising but is not yet a complete draft room.

Final target:

## Pre-draft
- select active league
- select owner draft slot if Sleeper has not assigned it
- choose mock mode
- choose bot speed / simulation behavior

## Draft board
For Fantasy Gamers:
- 10 team columns
- 15 round rows
- each pick cell shows player / position / team
- owner column highlighted
- current pick highlighted
- recent picks visible
- drafted players never disappear from history
- click team to inspect roster

## Available player panel
- NWR rank
- ADP
- expected round/pick
- NWR vs ADP
- make-it-back probability
- overall tier
- positional tier
- roster fit
- Best Available
- Best Fit
- Upside
- Safer
- Wait / Take Now guidance

## CPU teams
CPU teams should approximate market drafting rather than simply clone NWR rankings.

Candidate ingredients:
- ADP distribution
- stochastic variance
- roster construction
- position need
- position runs
- tier cliffs
- league format
- deterministic seeded simulation for reproducibility

## Live Sleeper companion
Eventually:
- Sleeper real pick
- local NWR draft board updates
- drafted asset removed from availability
- owner recommendations refresh
- no automated Sleeper selections

---

# 8. Tiering

Current Redraft tier behavior is not useful.

Known owner complaint:
- one player in Tier 1
- huge numbers of players in later tiers such as Tier 14

This defeats the purpose of draft tiers.

Candidate repositories:
- `aptmac/fftiers-python`
- `SuperFamousGuy/AutoTiers`
- `adesmarais944/tierforge`
- `richrliu/ff-tiers`
- `abhinavk99/espn-borischentiers`

## Required audit
Compare:
- existing NWR tier logic
- adjacent value-gap detection
- clustering
- Gaussian mixture approaches
- quantile methods
- position-specific tiering
- draft-round aware tiers

## Possible presentation
Broad tiers with subtiers:
- Tier 1A
- Tier 1B
- Tier 1C
- Tier 2A
- Tier 2B
- etc.

The letter subdivision is a presentation choice.
The actual boundaries must come from real value separation, not arbitrary fixed sizes.

NWR should support both:
- Overall Draft Tier
- Positional Tier

---

# 9. Waiver Wire

Waiver Wire is in final-scope candidate status.

Candidate repositories:
- `kkaeshav25/Fantasy-Football-Waiver-Wire-Model`
- `playjukeff/wire-room`
- `cmhlywa1-dev/thewaiverwire`
- `Osborw/waiver-wired`
- `coolnipunj/Sports-Waiver-Selector`
- `ffverse/ffscrapr`

## Desired final behavior
NWR knows:
- active Sleeper league
- current owner roster
- all rostered players
- actually available free agents
- league scoring
- position needs

Owner-facing outputs:
- `ADD NOW`
- `ADD`
- `STASH`
- `STREAM`
- `HOLD`
- `DROP`
- `DO NOT DROP`

Potential view:
- available player
- NWR value
- weekly production context
- rest-of-season context
- dynasty context where applicable
- roster fit
- recommended drop
- FAAB guidance only if a defensible method exists
- evidence / uncertainty

Dynasty and Redraft waiver logic must remain distinct.

---

# 10. Streamer Tool

Streamer is broader than K/DST.

Potential positions:
- QB
- TE
- K
- DST
- possibly FLEX-depth in shallow leagues

Inputs should include where available:
- actual Sleeper availability
- weekly projections / rankings
- opponent
- home/away
- bye
- near-term schedule
- current starter
- uncertainty

K/DST can remain external-consensus driven unless NWR eventually admits its own models.

Weekly streamer tools should answer:
- who is available?
- who should I add?
- who should I start?
- who can I drop?
- does this solve only this week or multiple weeks?

---

# 11. Weekly Lineup / Start-Sit

Candidate repositories:
- `evanng07/FantasyFootballOptimizer`
- `nqsullivan/fantasy-football-lineup-opitmizer`
- `djsensei/lineup_optimizer`
- `uberfastman/fantasy-football-metrics-weekly-report`
- `logan-cooper/ffcompanion`

Final target:
- active league roster
- legal lineup requirements
- recommended starting lineup
- close calls
- bench alternatives
- bye/injury warnings
- confidence
- matchup/weekly evidence
- explicit reasoning

No automatic roster writes unless separately authorized in the future.

---

# 12. Trade Tools

NWR already has significant Trade infrastructure and should not be replaced casually.

Existing strengths to preserve:
- Trade Decision Assistant
- advisory recommendations
- opponent roster awareness
- current roster/pick ownership when verified
- rookie ↔ veteran multi-authority context
- Immediate Production Context
- Medium-Term Research Outlook
- no hidden package score
- no autonomous trade execution

Candidate external repositories:
- `mattkjones/4-keeper-sleeper-ff-trade-machine`
- `jackmunhall/fantasy-football-trading-calculator`
- `abirney/fantasy-football-trade-calculator`
- `Eric-Vondunn/fantasy-trade-calculator`
- `Joe11223311/league-market`

Audit them primarily for:
- UX
- trade construction
- opponent roster targeting
- counter generation
- consolidation/premium concepts
- positional replacement
- trade finder concepts

## Final candidate trade tools
- Trade Analyzer
- Trade Finder
- Counteroffer Generator
- Opponent Roster Targets
- Contender/Rebuilder context
- Win-now impact
- medium/long-term impact
- market disagreement
- rookie ↔ veteran context

Do not import a generic calculator as the decision authority if NWR's own system is stronger.

---

# 13. Market

Market should become a first-class decision surface.

Existing NWR Market must be fully audited before new construction.

Potential final fields:
- NWR value / rank
- Market value
- Market rank
- ADP
- expected draft pick
- NWR vs Market
- NWR vs ADP
- source
- source date
- stale/fresh status
- buy/sell/fade/value interpretation
- movement over time if lawful

Market context is useful for:
- Dynasty trades
- Redraft Beat ADP
- trade targeting
- waiver opportunity
- draft timing

Market is not automatically NWR truth.

---

# 14. Full Fantasy Assistant / MCP Repositories

High-priority candidates:
- `gtonic/nfl_mcp`
- `derekrbreese/fantasy-football-mcp-public`
- `carterfawson/fantasy-football-mcp`
- `Kbtimko/dynasty-mcp`
- Sleeper MCP implementations:
  - `FloSchl8/sleeper-mcp`
  - `swcollard/sleeper-mcp`
  - `gmendonc/sleeper-mcp-server`
  - `jfriend615/sleeper-fantasy-football-mcp`
  - `anthonybaldwin/sleeper-api-mcp`

These should be audited as broad capability maps:
- what tools do they expose?
- what workflows do they solve?
- what are we missing?
- do they have reusable interfaces or patterns?
- do they duplicate NWR?
- should any capability become an internal NWR service/tool?

---

# 15. Core Data Repositories

High-priority:
- `nflverse/nflverse-data`
- `nflverse/nflverse-pbp`
- `nflverse/nflverse-rosters`
- `nflverse/nflverse-players`
- `nflverse/nflreadpy`
- `nflverse/nflfastR`
- `nflverse/ngs-data`
- `nflverse/nflverse-pfr`
- `ffverse/ffopportunity`
- `dynastyprocess/data`

Before adoption:
- confirm license
- confirm allowed use
- confirm freshness
- confirm current/historical parity
- confirm NWR already has/does not have the same source
- respect prior provider/source governance rules

Do not reopen prohibited/opaque DynastyProcess inspection without explicit authorization.

---

# 16. Product Surfaces the Final Version Should Be Evaluated Against

## Draft
- Rankings
- Draft Board
- Mock Draft
- Live Sleeper Companion
- Beat ADP Pool
- Make-It-Back Probability
- Positional Runs
- Tier Cliffs
- My Roster
- Every-Team Rosters
- Draft Log
- Queue / Targets

## Team Management
- Weekly Lineup
- Start/Sit
- Waiver Wire
- Streamers
- Drop Candidates
- Injury / Availability Watch
- Bye-Week / Roster Problems

## Market
- NWR Value
- Market Value
- ADP
- NWR vs Market
- NWR vs ADP
- Buy / Sell / Fade / Value
- Movement / freshness

## Trades
- Trade Analyzer
- Trade Finder
- Counteroffers
- Opponent Roster Targets
- Win-Now Impact
- Medium/Long-Term Context
- Rookie ↔ Veteran Context

## Analysis
- Rankings
- Player Detail
- Player Compare
- Dynasty Outcomes
- Rookie Review
- Statistical explanation
- Research context
- uncertainty / caveats

## Planning
Preserve the existing owner planning tools:
- Roster Planner
- Future Pick Planner
- Upcoming Draft Prep
- Keeper Prep
- Drop Prep
- Trade Deadline Prep
- Scenario Playground
- Decision Tracker

---

# 17. Dynasty vs Redraft Authority Rules

## Redraft
Rookies and veterans can share the governed current-season Redraft projection board.

Use that common scale for:
- draft rankings
- win-now comparison
- start/sit where current-season method applies
- roster construction
- draft recommendation

## Dynasty
Rookie Review Score and Finished V1 Veteran Score are NOT directly comparable.

Current mixed Rookie ↔ Veteran Compare must remain multi-authority:
- Win Now: Production
- Dynasty Today: Research Only / Insufficient
- 3Y: Research Only / Insufficient
- 5Y: Research Only / Insufficient
- Safety
- Upside
- Uncertainty
- concise Why

Do not invent 0–100 Horizon Value until future validation succeeds.

---

# 18. Key Known Watch Items

Preserve the NWR owner watchlist:
- elite young players with short NFL history
- elite TE small-gap cases
- major offseason role changes
- volume-heavy veterans
- stale market context
- current injury/team changes
- rookie authority differences
- 1QB quarterback economics

Known current examples such as Bowers / Jeanty / Sutton are diagnostic cases, not tuning targets.

---

# 19. Immediate Next Phase

**Do not implement Draft Room V2, Beat ADP, Waivers, Streamers, or Trade Finder yet.**

The immediate next mission is:

# NWR COMPLETE CAPABILITY + EXTERNAL REPOSITORY ADOPTION AUDIT V1

It must:

1. Recover the strongest current NWR Desktop candidate.
2. Audit the entire NWR repository and current artifacts for relevant existing capability.
3. Deep-inspect the high-priority external repositories above.
4. Verify licenses and freshness.
5. Inventory current APIs/providers already implemented.
6. Inventory all existing NWR Market/ADP/Sleeper/draft/tier/waiver/trade/weekly capabilities.
7. Compare NWR vs external implementations feature by feature.
8. Produce a final:
   - capability matrix
   - source/provider matrix
   - external repo adoption matrix
   - duplication map
   - gap map
   - target architecture
   - implementation sequence
9. Do NOT implement features during the audit except tiny probes required to establish facts.
10. Return an owner approval packet for the final completion plan.

---

# 20. Desired Audit Output

The audit should end with a table such as:

| Final Capability | Best Existing NWR Asset | Best External Candidate | Decision | Work Needed |
|---|---|---|---|---|
| Draft Board | ... | ... | Upgrade NWR | ... |
| CPU Mock | ... | ... | Adapt pattern | ... |
| ADP | ... | ... | Reconnect existing | ... |
| Beat ADP | ... | ... | Build from NWR + ADP | ... |
| Tiers | ... | ... | Replace current tiering | ... |
| Waiver Wire | ... | ... | Extend existing | ... |
| Streamer | ... | ... | ... | ... |
| Weekly Lineup | ... | ... | ... | ... |
| Trade Analyzer | Existing NWR | external UX only | Keep/upgrade | ... |
| Trade Finder | ... | ... | ... | ... |
| Market | Existing NWR | ... | Reconnect/upgrade | ... |

And then one final implementation roadmap:
- Phase 0: required shared data/contracts
- Phase 1: Draft Room / ADP / tiering
- Phase 2: Weekly / Waivers / Streamers
- Phase 3: Trades / Market integration
- Phase 4: owner acceptance / final Desktop publication

The phases may change after the audit.
They must be evidence-driven.

---

# 21. Non-Negotiable Guardrails

- Reuse NWR first.
- No hidden universal trade package score.
- No automatic trades.
- Sleeper remains read-only unless explicitly changed later.
- Missing data stays UNKNOWN, not zero.
- Research remains labeled Research Only.
- External consensus is not NWR model authority.
- No model promotion without validation.
- No current-player tuning.
- Do not train to consensus/market.
- Preserve local owner data.
- No destructive Git operations.
- Isolated worktrees for implementation lanes.
- No force pushes.
- No canonical publication without explicit owner approval.
- Scheduler remains disabled unless explicitly approved.
- Streamlit remains fallback/development UI until Desktop is fully accepted.
- Do not inspect or use opaque DynastyProcess files without explicit authorization.
- Do not introduce paid/provider dependencies silently.
- Verify license before copying external code.

---

# 22. Definition of "Complete NWR"

NWR is not complete because tests are green.

It is complete when the owner can actually:

## Before the draft
- open the right league
- understand league-specific rankings
- see NWR vs market
- identify Beat ADP targets
- understand tiers/cliffs
- prepare draft targets

## During the draft
- see the full board
- see every pick
- select a draft slot
- have realistic CPU behavior in mocks
- receive roster-aware recommendations
- know whether a target will likely make it back
- use a live read-only Sleeper companion

## During the season
- see the recommended lineup
- resolve close start/sits
- find available waiver adds
- know who to drop
- stream positions
- monitor roster weaknesses
- understand injuries/availability

## For trades
- compare players
- compare rookies/veterans truthfully
- inspect opponent rosters
- build/find trades
- receive counteroffers
- understand immediate vs medium/long-term effects
- understand NWR vs market disagreements

## For Dynasty
- manage the roster
- manage future picks
- evaluate rookies
- evaluate veterans
- compare rookie/veteran assets
- plan contention/rebuild windows
- use Scenario Playground and Decision Tracker

And all of this must be understandable under real owner use—not merely technically available somewhere in the repository.

---

# 23. Source-of-Truth Rule

This document is the planning source of truth for the next NWR completion phase.

If later work conflicts with it:
1. stop;
2. identify the conflict;
3. explain why the plan should change;
4. obtain owner approval;
5. update the canonical plan.

Do not silently drift away from this plan.
