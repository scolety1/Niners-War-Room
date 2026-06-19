# Trading Lab Manual Review Packet Examples

Date: 2026-06-18

## Purpose

These fake examples show ACCEPT, HOLD, and REJECT outcomes for manual review
packets. They are not recommendations, signals, or investment advice.

## Guardrail Checklist

- Public source cited or HOLD.
- Paper-only status explicit.
- No private account data.
- No credentials, secrets, keys, tokens, cookies, or `.env`.
- No broker/API or order endpoint.
- No automated execution.
- No production advice.
- No data ingestion or generated output.
- No app/deployment/fantasy-lane path.

## Valid Packet 1

| field | value |
| --- | --- |
| packet_id | `MRP-ACCEPT-001` |
| artifact_type | Research intake |
| research_item_id | `RI-EXMPL-001` |
| summary | Public filing research question with manual citation. |
| result | ACCEPT |
| why | Public-source, paper-only, no prohibited content. |

## Valid Packet 2

| field | value |
| --- | --- |
| packet_id | `MRP-ACCEPT-002` |
| artifact_type | Watchlist note |
| research_item_id | `WL-PAPER-002` |
| summary | Fictional `PAPER` note with public source names and risk notes. |
| result | ACCEPT |
| why | Paper-only hypothesis and invalidation condition present. |

## Valid Packet 3

| field | value |
| --- | --- |
| packet_id | `MRP-ACCEPT-003` |
| artifact_type | Risk journal |
| research_item_id | `RJ-SIM-003` |
| summary | Bias and source-quality risks for a manual research note. |
| result | ACCEPT |
| why | Descriptive risk review without advice or execution. |

## Invalid Packet 1

| field | value |
| --- | --- |
| packet_id | `MRP-REJECT-001` |
| summary | Buy `EXMPL` now after source review. |
| result | REJECT |
| why | Production advice and real-money instruction. |

## Invalid Packet 2

| field | value |
| --- | --- |
| packet_id | `MRP-REJECT-002` |
| summary | Connect broker and use API key to review account holdings. |
| result | REJECT |
| why | Broker/API, credential, and private account language. |

## Invalid Packet 3

| field | value |
| --- | --- |
| packet_id | `MRP-REJECT-003` |
| summary | Auto-execute and write generated market dataset for review. |
| result | REJECT |
| why | Automated execution and generated-output/data-ingestion language. |

## HOLD Example

| field | value |
| --- | --- |
| packet_id | `MRP-HOLD-001` |
| summary | Public-looking source with unclear terms. |
| result | HOLD |
| why | Terms and storage policy need manual review before use. |
