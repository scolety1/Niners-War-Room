# Draft UX Product Reset

Phase 1 replaces the old Draft Room concept with two focused draft surfaces.
The old mixed-board implementation stays available as a hidden debug page, but it
should not be the default live draft experience.

## Pages

### Rankings

Purpose: fast review of the draftable player pool.

First view:

- one ranked table
- player search
- position filter
- asset-type filter
- confidence/warning columns

Do not show old audit tabs, source plumbing, or mixed strategy tables on the first
view. Receipts and comparisons can live behind expanders or links.

### Draft Board

Purpose: live and mock draft operation.

First view:

- 5 round x 10 team pick grid
- current pick
- highlighted Niners picks
- recently drafted players
- best remaining options when the Niners are on the clock

The board should feel like a click-first draft tracker, not a report.

## Available Player Pool

The draftable pool comes from:

- rookies from `fact_rookie_draftables.csv`, rookie model outputs, or the unified
  asset board
- released veterans actually marked available in `fact_available_veterans.csv`
  or roster status
- free agents actually marked available in `fact_available_veterans.csv` or
  roster status
- manual draftable players in `fact_manual_draftables.csv`

Likely forced releases are watchlist items only. They must not enter the combined
draft pool until the data marks them released, free agent, or manually draftable.

Protected roster players must be excluded unless they are explicitly included in
the manual draftables file.

## Pick Grid

The live board uses 50 picks:

- 5 rounds
- 10 teams
- overall pick 1-50
- round pick 1-10

Each pick cell eventually stores:

- pick number
- current owner
- original owner
- drafted player
- drafted position
- edit status

## Mock Draft State

Mock state is session-local first:

- drafted pick assignments
- drafted player IDs
- available pool derived from rankings minus drafted players
- current pick pointer

Later phases add JSON save/load under `local_exports/mock_drafts`. Mock files must
never mutate source data packs or model outputs.

## My-Pick Detection

The board detects Niners picks by matching current pick owner against the configured
team id/name. If ownership is ambiguous, the pick should be marked review-needed
rather than silently treated as ours.

## Best Options At Pick

Best options are derived from the current available pool after drafted players are
removed. The first version sorts by draft value, confidence, and player name. Later
phases add reach/value labels, roster context, and warning-aware tie breakers.

## Safety

While model calibration is blocked, Rankings and Draft Board may show pool status
and pick inventory, but they must not present model order as decision-ready.

## User Feedback Repair Queue - 2026-05-08

These items came from live app review and should be fixed before calling the
draft workflow decision-ready.

### Real Draft Pool Before Fun Mock Drafts

Mock drafts and Rankings are not useful until the available pool reflects the
actual offline draft room. The app must load or clearly import:

- the real current-year rookie board
- actually released veterans
- actual free agents
- manually added draftable players when the league room has special cases

Fixture/demo rookies must stay visibly labeled as review-only and should not be
presented as the normal pool.

### Pressure Must Measure Pain, Not Just Rule Count

The current Keeper Pressure table is too flat because every team has the same
top-five release count. Pressure should be based on the quality gap between the
forced-release candidate and the team's easy non-top-five drops.

Required behavior:

- A team with an obvious weak top-five release should show low pressure.
- A team whose top-five players are all strong should show high pressure.
- The pressure score should include forced-release candidate value, next-best
  protected value, roster bubble alternatives, and whether a non-forced release
  would be easier.
- The table should explain the actual pain point, not repeat that every team has
  one required release.

### League Targets Must Show Opportunity

League Targets should not show flat keeper management for every opponent. It
should classify targets by acquisition opportunity:

- likely forced releases
- expensive targets
- cheap targets
- market-edge targets
- avoid

Former "shield" language is misleading when the player would be expensive. A
shield target should mean a cheaper player who helps another team solve a
top-five release problem, not a superstar who would cost a premium.

### End-of-Cycle Bug/Customization Pass

Keep building the website in safe review-only mode for now. Deeper bug cleanup,
labels, customization, and final UX tuning should happen after the core pool,
pressure, and target logic are repaired.
