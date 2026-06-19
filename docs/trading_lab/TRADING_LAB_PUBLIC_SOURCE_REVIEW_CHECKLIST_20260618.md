# Trading Lab Public Source Review Checklist

Date: 2026-06-18

## Purpose

Use this checklist before referencing a public source in Trading Lab research.
Approval means the source may be cited in paper/research-only notes. It does
not approve data ingestion, generated outputs, broker/API use, deployment, or
investment advice.

## Checklist

| check | pass expectation |
| --- | --- |
| Public availability | Source can be reviewed without private account access or credentials. |
| Attribution expectations | Source name, URL or citation, review date, and data period can be recorded. |
| License/terms review note | Any usage, redistribution, or scraping limitations are noted. |
| Refresh cadence | Manual review cadence is stated; automated refresh is not approved. |
| Data sensitivity | Source is public or manually written paper-only material. |
| Storage policy | Raw downloads, generated files, caches, logs, and exports stay untracked. |
| Manual review requirement | Human review is required until a later explicit phase gate. |
| Private account data absent | No balances, holdings, statements, fills, or account exports are involved. |
| Credentials absent | No keys, tokens, passwords, cookies, broker auth, or `.env` files are needed. |
| Education/research-only use | Source is used only for learning, attribution, notes, or paper design. |

## Pass Examples

| source | verdict | reason |
| --- | --- | --- |
| SEC EDGAR filing page | PASS | Public source with citation, filing date, and manual review path. |
| FRED public series page | PASS | Public economic source; manual citation only. |
| Exchange symbol reference page | PASS | Public reference page for paper-only labels. |
| Manually written paper note with public citations | PASS | No private account data or generated output. |

## Fail Examples

| source | verdict | reason |
| --- | --- | --- |
| Broker account export | FAIL | Private account data and real holdings may be present. |
| Token-protected API feed | FAIL | Credentials and API integration are not approved. |
| Real-money order history | FAIL | Execution data is prohibited. |
| Paid/private dump without explicit approval | FAIL | Restricted data requires a later phase gate. |
| `.env` file | FAIL | Secret storage is prohibited. |

## Review Result

Use one of these statuses:

- `PASS_PUBLIC_RESEARCH_ONLY`
- `HOLD_NEEDS_TERMS_REVIEW`
- `HOLD_NEEDS_STORAGE_POLICY`
- `FAIL_PRIVATE_OR_SECRET`
- `FAIL_EXECUTION_OR_ADVICE_RISK`

## Safe Use Reminder

Passing this checklist permits citation in research notes only. It does not
permit ingestion jobs, broker access, execution, private account analysis,
generated artifacts, deployment, or personalized investment advice.
