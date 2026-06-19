# Trading Lab Desktop UI Spec

Date: 2026-06-18

## Header

- Page title: Trade Lab
- Subtitle: Find realistic fantasy trades where market says fair, but NWR says
  we win.

## Desktop-First Layout

Trading Lab should use a three-column desktop layout:

- Left control panel: trade intent, players, opponent, package constraints, and
  risk preferences.
- Center results: best trade, ranked package cards/table, negotiation ladder,
  bad trade warnings, and review cards.
- Right context panel: roster aftermath, keeper impact, drop pressure, rookie
  pick context, opponent fit, and data status.

## Modes

- Trade For Player
- Trade Away Player
- Upgrade Position
- Consolidate Depth
- Pick Conversion
- Drop-Pressure Trade
- Opponent-Fit Trade
- Training Mode

## Left Control Panel

- Mode selector
- Target player
- Outgoing player
- Opponent team
- Include picks toggle
- Allow multi-player packages toggle
- Untouchable assets
- Max offer aggressiveness
- Risk preference
- Win-now vs long-term preference

## Center Results

### Best Trade Card

The best trade card should show:

- Package summary
- NWR value delta
- Public fantasy market fairness
- Opponent fit
- Roster impact
- Risk flags
- Manual review verdict

### Ranked Package Table Or Cards

Rank packages by:

- NWR value gain
- Public fantasy market realism
- Opponent fit
- Roster impact
- Keeper/drop pressure effect

### Negotiation Ladder

Show:

- Opening offer
- Fair offer
- Max offer
- Walk-away line

### Bad Trade Detector

Warn when:

- NWR value delta is negative.
- Public fantasy market value says the offer is unrealistic.
- Opponent fit is weak.
- Keeper or drop pressure gets worse.
- Rookie pick cost is too high.

### Trade Review Cards

Each card should explain why a package is realistic or risky.

## Right Context Panel

- Roster aftermath
- Keeper impact
- Drop pressure impact
- Positional depth impact
- Rookie/mock draft context placeholder
- Opponent fit
- Data status / needs data

## Data Status / Needs Data

MVP data should be fake and in-memory. Real NWR value, public fantasy market
value, roster, drop pressure, rookie board, and mock draft integration remain
future work.

## Training Mode Placeholder

Training Mode should provide practice scenarios and score:

- NWR value
- Market realism
- Opponent fit
- Roster impact
- Negotiation quality

## MVP Scope

- Static/fake in-memory trade packages.
- Desktop-first component or isolated page.
- Manual review labels.
- No persistence.
- No integration with real fantasy source data.

## Future Scope

- Integrate NWR private value outputs.
- Compare against public fantasy market value sources.
- Include roster, keeper, drop, rookie, and mock draft context.
- Add team-by-team opponent fit once data integration is approved.

## Explicit Non-Goals

- Stock trading or finance workflows.
- Broker/API integration.
- Real-money trading.
- Investment advice.
- Automated fantasy trade submission or acceptance.
- Data ingestion.
- Public fantasy trade-value API integration.
- Real Outcome, Rookie, Mock Draft, or Drop Decision integration.
- Deployment.
