# Trading Lab Source Inventory Template

Date: 2026-06-18

## Purpose

This template is for Trading Lab research and source review only. It helps
future agents describe public or manually written research sources before any
code, data ingestion, generated output, simulation tooling, or private account
handling exists.

This template is research only and not investment advice. It creates no
execution path, broker integration, order workflow, account connection,
credential storage, or deployment path.

Do not store secrets, credentials, keys, tokens, `.env` files, private account
data, broker exports, real-money order history, paid/private data dumps, or
generated artifacts in this repo.

## Required Fields

Each source inventory row should include:

- `source_name`
- `source_type`
- `access_type`
- `data_sensitivity`
- `allowed_use`
- `prohibited_use`
- `attribution_required`
- `storage_policy`
- `refresh_policy`
- `review_status`
- `notes`

## Validation Expectations

Each row should pass these checks before it is accepted as a Trading Lab source
inventory note:

- Source is public, manually written, or simulated/paper-only.
- Source does not require broker credentials, account keys, API tokens, live
  secrets, private account access, or `.env` files.
- Source is not real-money order history, brokerage account export data, or an
  automated trading endpoint.
- `allowed_use` is limited to research, education, source review, paper notes,
  watchlist notes, risk journaling, or future paper simulation design.
- `prohibited_use` explicitly blocks real-money trading, broker orders,
  automated execution, production investment advice, deployment, and secret
  storage.
- `storage_policy` keeps local raw data, generated files, data directories,
  caches, logs, exports, archives, and secrets untracked.
- `attribution_required` identifies the public source or states that the note is
  manually written.

## Allowed Example Rows

These examples are fake/public-only examples. They are not endorsements,
recommendations, or instructions to trade.

| source_name | source_type | access_type | data_sensitivity | allowed_use | prohibited_use | attribution_required | storage_policy | refresh_policy | review_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC EDGAR public filings | public_company_filings | public website review | public | Education and research notes about filings | Trading advice, broker orders, automated execution, private account decisions | Cite company filing, form type, filing date, and SEC URL | Do not store raw downloads in repo; docs may cite public URLs | Manual review only until a later approved phase | Allowed example | Public filings may support source review and paper-only research questions. |
| FRED public economic data | public_economic_data | public website review | public | Education and macro context notes | Trading signals, execution triggers, production advice | Cite FRED series name, series ID, review date, and URL | Do not commit downloaded datasets or generated charts | Manual review only until a later approved phase | Allowed example | Use for context and learning, not instructions to buy or sell. |
| Exchange-published symbol reference page | public_market_reference | public website review | public | Symbol/reference verification for watchlist notes | Broker routing, order placement, live execution | Cite exchange page, symbol, review date, and URL | Do not ingest or cache market data in repo | Manual review only until a later approved phase | Allowed example | Reference pages may help normalize paper-only watchlist labels. |
| Manually written paper-research note | manual_paper_research | local markdown note | non-private manual note | Paper-only hypothesis, risk note, and learning journal | Real-money trade instruction, account sizing, private account decision | Note author/date and public sources reviewed | Keep in approved docs path only; no raw data or private account fields | Human-authored review cadence | Allowed example | Notes must remain paper-only and not personalized investment advice. |

## Prohibited Example Rows

These rows are intentionally invalid. They must not be added as accepted source
inventory entries.

| source_name | source_type | access_type | data_sensitivity | allowed_use | prohibited_use | attribution_required | storage_policy | refresh_policy | review_status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Broker API credentials | broker_credentials | credential file or broker portal | secret | None | All use prohibited | Not applicable | Do not store, stage, commit, or template | Never | PROHIBITED | Credentials, keys, tokens, and broker auth material are forbidden. |
| Private brokerage account exports | private_brokerage_data | account download | private account data | None unless a later explicit approval exists | Commit, analysis, execution, sharing, or generated outputs | Not applicable | Do not store in repo | Never | PROHIBITED | Private balances, holdings, fills, statements, and exports are blocked. |
| Real-money order history | real_money_execution_data | account download or broker API | private execution data | None | Research import, backtest seed, advice, execution, or examples | Not applicable | Do not store in repo | Never | PROHIBITED | Real-money fills/orders must not enter Trading Lab. |
| `.env` files | secret_storage | local environment file | secret | None | Any repo storage or sample secret workflow | Not applicable | Do not create or commit | Never | PROHIBITED | `.env` files and secret templates are blocked. |
| Paid/private data dump without approval | private_paid_data_dump | vendor portal or export | private or restricted | None until explicit later approval | Commit, redistribution, model input, generated output, or advice | Not applicable until approved | Do not store in repo | Never in T1/T2 foundation | PROHIBITED | Paid/private dumps need a later phase gate and are blocked here. |

## Safe Use Reminder

Source inventory rows may support learning, research planning, attribution
hygiene, and later paper simulation design only. They must never become
investment advice, broker instructions, execution triggers, credential
configuration, or deployment inputs.
