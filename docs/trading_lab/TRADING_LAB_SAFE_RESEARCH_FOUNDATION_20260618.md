# Trading Lab Safe Research Foundation

Date: 2026-06-18

## Purpose

This note documents the first safe post-migration Trading Lab coding foundation.
The foundation is local-only, research-only, and paper/simulation-only. It
creates source inventory and watchlist-note contracts with validation guardrails.

It does not create trading execution, broker connectivity, data ingestion,
automation, recommendations, deployment, generated artifacts, or private account
handling.

## Added Foundation

Trading Lab now has a small Python module under `src/trading_lab/` for:

- Source inventory metadata validation
- Allowed source category checks
- Prohibited source category checks
- Prohibited execution-language checks
- Secret-like config field checks
- Paper-only watchlist-note validation

The module is intentionally boring. It validates metadata and contracts; it does
not fetch data, parse market feeds, connect to brokers, run backtests, place
orders, or emit recommendations.

## Paper-Only Scope

Allowed Trading Lab research remains limited to:

- Education and research notes
- Public source inventory
- Public market data notes
- Public company filing notes
- Public economic data notes
- Public news and research notes
- Manually entered paper-trade journals
- Simulated portfolio and watchlist concepts
- Backtesting design questions
- Risk journal structure

All watchlist notes must be labeled paper-only. Metrics and observations are
descriptive research aids, not investment advice.

## Prohibited Behaviors

Trading Lab must not add:

- Real-money trading
- Broker orders
- Broker API trading integration
- Credentials, secrets, keys, or tokens
- Automated execution
- Production investment advice
- Public deployment
- Secret storage
- Private account data unless explicitly approved
- Data ingestion code
- Backtest execution code
- Generated artifacts

The validation module blocks prohibited source categories, secret-like config
fields, and common broker/order/execution phrases in source metadata and
watchlist notes.

## Source Inventory Contract

A research source record should include:

- `source_id`: stable local identifier
- `name`: human-readable source name
- `category`: one allowed Trading Lab source category
- `intended_use`: one allowed research or paper-only use
- `access_method`: non-credentialed public/manual access description
- `attribution`: source attribution expectations
- `reviewed_on`: optional `YYYY-MM-DD` review date
- `notes`: optional research-only notes
- `config`: optional non-secret metadata

Allowed source categories:

- `public_market_data`
- `public_company_filings`
- `public_economic_data`
- `public_news_research`
- `manual_paper_trade_journal`
- `simulated_portfolio_watchlist`

Prohibited source categories:

- `broker_credentials`
- `account_keys`
- `private_brokerage_data`
- `real_money_execution_data`
- `automated_trading_endpoint`
- `secrets`

## Watchlist Note Contract

A watchlist note should include:

- `symbol`
- `research_theme`
- `hypothesis`
- `public_sources`
- `risk_notes`
- `paper_only`
- `review_date`

Watchlist notes must use public source citations, keep `paper_only` set to
true, and avoid any broker/order/execution language. They must not include real
holdings, account sizes, order instructions, private brokerage data, or
production advice.

## Future-Agent Safety Rules

Future agents should add research safely by following this order:

1. Update docs before adding new source or data behavior.
2. Add validation tests before broadening allowed source categories.
3. Keep all raw data, generated outputs, logs, caches, archives, and exports
   untracked.
4. Avoid `.env` files and credential templates.
5. Avoid broker packages, API clients, and trading endpoints.
6. Keep Trading Lab separate from Master, Outcome, Rookie, Mock Draft, Drop
   Decision, and Deployment V2 lanes.
7. Stop if a request asks for real-money execution, broker orders, credentials,
   secrets, deployment, or production investment advice.

Future data ingestion, source inventory files, simulation tooling, notebooks,
or generated research outputs require a separate explicit phase gate before any
code or files are created.
