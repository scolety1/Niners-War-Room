# Trading Lab Source Inventory Validation Examples

Date: 2026-06-18

## Purpose

These examples define expected source inventory validation outcomes for
paper/research-only Trading Lab work. They do not approve data ingestion,
generated outputs, broker/API access, credentials, execution, deployment, or
investment advice.

## Examples

| example | source_type | expected_result | why |
| --- | --- | --- | --- |
| SEC EDGAR public filing page | Public company filing | ACCEPT | Public source, citeable, manual review, no secrets, no account data. |
| FRED public economic series page | Public economic data | ACCEPT | Public data source for education/research context with attribution. |
| Manually written paper note with public citations | Manual paper note | ACCEPT | Human-authored research note with no private account fields. |
| Exchange symbol reference page | Public market reference | ACCEPT | Public reference only, not a signal or execution path. |
| Terms unclear for a public calendar page | Public news/reference | HOLD FOR MANUAL REVIEW | Public-looking source needs usage/terms review before citation. |
| Paid/private data dump without approval | Restricted/private data | HOLD FOR MANUAL REVIEW | Requires later explicit approval; not allowed in T3. |
| `.env` file with token | Secret storage | REJECT | Secrets and `.env` files are prohibited. |
| Broker API key or token | Credential source | REJECT | Credentials, keys, tokens, and broker access are prohibited. |
| Private brokerage account export | Private brokerage data | REJECT | Private account data is prohibited. |
| Private account balance screenshot | Private account data | REJECT | Account balances and screenshots are prohibited. |
| Auto-execution endpoint description | Execution endpoint | REJECT | Automated execution and order endpoints are prohibited. |

## Expected Validation Rules

- ACCEPT only public, manually reviewed, or paper-only sources.
- HOLD when terms, permissions, storage policy, or source status are unclear.
- REJECT secrets, credentials, broker exports, private account data, execution
  endpoints, real-money order history, and automation triggers.

## Safe Use Reminder

Accepted source inventory examples may support research notes only. They must
not become investment advice, broker instructions, ingestion jobs, generated
datasets, or deployment inputs.
