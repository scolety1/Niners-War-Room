# Trading Lab Integration Seam Review Packet - 2026-06-18

## How To Open The Page

- Isolated Streamlit page: `app/pages/11_trade_lab.py`

## What Is Fixture-Backed

- Fantasy value contracts.
- Fixture value provider.
- Fixture candidate package builder.
- Fixture scoring.
- Fixture negotiation ladder.
- Fixture roster aftermath.
- Fixture warning engine.
- Fixture package comparison rows.
- Fixture Trade Away target board.
- Fixture Trade For offer board.

## Integration Seams

- `ValueProvider`
- `PublicMarketProvider`
- `RosterContextProvider`
- `DropPressureProvider`
- `RookieContextProvider`
- `MockDraftContextProvider`
- `OpponentContextProvider`

All current providers are fixture-only or placeholders. Real integrations are not wired.

## Provenance Labels

- Fixture demo value.
- Real NWR integration not wired.
- Public fantasy market source not wired.
- Manual review required.

## Missing Data Behavior

Missing NWR values, public market values, roster context, drop pressure, rookie/mock context, opponent context, unsupported modes, no packages, and all-assets-excluded states return clear placeholder labels.

## Explanations

Package explanations cover NWR edge, public fantasy market fairness, opponent fit, roster impact, keeper/drop impact, and risk notes. Explanations are review notes only.

## Trade-Away Board Status

Trade Away mode has fixture-backed categories for best NWR return, most realistic return, win-now return, long-term return, pick-heavy return, player-heavy return, and do-not-accept-below line.

## Trade-For Board Status

Trade For mode has fixture-backed categories for cheapest plausible opener, fair offer, aggressive offer, max offer, player-only offer, pick-heavy offer, do-not-include assets, and sweetener suggestions.

## Review Queue Placeholder Status

The review queue is a non-persistent placeholder. It is not wired, not saved, and creates no generated artifacts.

## Not Wired

- Real NWR private values.
- Public fantasy market data sources.
- Real roster context.
- Real keeper/drop pressure context.
- Rookie and Mock Draft context.
- Saved review queue.

## Blocked

- Data ingestion.
- Public fantasy source APIs.
- Cross-lane imports or edits.
- Generated outputs.
- Automated trade submission.
- League transaction execution.
- Deployment.
- Any stock-market, broker, crypto, equity, or real-money finance work.
