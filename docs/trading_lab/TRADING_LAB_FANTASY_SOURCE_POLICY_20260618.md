# Trading Lab Fantasy Source Policy

Date: 2026-06-18

## Purpose

This policy defines future source categories for Fantasy Trade Lab. It does not
approve data ingestion, scraping, app wiring, or fantasy data integration.

## Allowed Future Source Categories

- NWR private value outputs
- Outcome V1 display values
- Rookie board values
- Drop Decision roster pressure
- Mock Draft pick/player context
- Public fantasy rankings
- Public dynasty trade calculators
- Public ADP
- Public dynasty market value
- Manually entered opponent roster context

## Prohibited Source Categories

- Stock market APIs
- Broker APIs
- Real-money account data
- Credentials or secrets
- Paid/private data unless explicitly approved later
- Scraping without approval
- Fantasy source values contaminating NWR private score

## Source Separation Rules

- Public fantasy values may be displayed as comparison or realism signals.
- NWR private value remains separate and must not be overwritten by public
  fantasy source values.
- Manually entered opponent roster context must be labeled as manual.
- Future source work requires explicit approval before ingestion or integration.

## Storage And Secrets

Do not commit credentials, secrets, tokens, account keys, generated artifacts,
or private paid source dumps.
