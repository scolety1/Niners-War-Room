# Trading Lab Source And Data Policy

Date: 2026-06-18

## Purpose

This policy defines source and data boundaries before any Trading Lab code,
data ingestion, simulation tooling, or generated artifacts exist.

The goal is to keep T1 research safe, reproducible, paper-only, and free of
secrets, credentials, private account data, broker execution paths, and
fantasy-lane changes.

## Allowed Source Categories

Trading Lab may plan around these source categories:

- Public market data
- Public company filings
- Public economic data
- Public news and research notes
- Manually entered paper-trade journals
- Simulated portfolio and watchlist files

Allowed public sources should be documented with enough attribution for a
future reader to understand where an observation came from, when it was
reviewed, and whether the source has redistribution or usage limits.

## Prohibited Source Categories

Trading Lab must not use, request, store, stage, commit, or design around:

- Broker credentials
- Account keys
- Private brokerage data
- Real-money execution data
- Automated trading endpoints
- Secrets
- Live credential files
- Account statements or balances
- Order history from real accounts
- Broker API trading integrations

No prohibited source may be included as a sample, placeholder, template, test
fixture, local note, copied output, screenshot, or generated artifact.

## No Secrets Policy

Secrets must not be committed or stored in this repo. This includes API keys,
tokens, passwords, private account identifiers, broker credentials, cookies,
session files, encrypted secret blobs, and sample secrets that resemble real
credential formats.

Docs may state that secrets are prohibited. Docs must not include sample secret
values or instructions that encourage adding secrets to the repo.

## No Credentials Policy

Trading Lab must not create `.env` files, credential templates, broker auth
flows, key-loading helpers, or account-connection instructions.

Future tooling, if ever approved, must avoid broker trading integration and
must pass a separate security and data-policy gate before any credential-like
configuration is considered.

## Private Account Data

Private account data is prohibited unless a later explicit approval exists.
This includes balances, holdings, account numbers, real order history, tax
forms, statements, fills, realized gains/losses, and brokerage exports.

T1 does not approve private account data. T1 may define paper-trade journal
fields and simulated portfolio concepts only.

## Public Data Attribution

When future research notes reference public data, they should capture:

- Source name
- Source URL or citation where appropriate
- Date reviewed
- Data date or reporting period when known
- Any usage limitation or redistribution warning
- Whether the note is an observation, hypothesis, or simulated result

Attribution does not convert a source into investment advice. All observations
remain education-only and paper-only.

## Local Generated Files

Local generated files must stay untracked unless a later explicit manifest
allows a specific non-secret artifact path.

The following must remain untracked and out of scope:

- `data/`
- `local_exports/`
- `.venv/`
- Caches
- Logs
- Generated artifacts
- Secrets

Generated research outputs, raw downloads, transformed datasets, screenshots,
exports, and notebooks are not part of T1. If a later phase proposes generated
outputs, it must define allowed paths, retention rules, redaction checks, and
commit rules before any files are created.

## T1 Source Inventory Boundary

T1 may create a docs-only inventory plan for public source categories and review
criteria. T1 must not ingest, scrape, download, transform, or commit market
data.

T1 remains GREEN only while it records policies and plans without touching
code, private data, broker systems, generated files, or fantasy football lanes.
