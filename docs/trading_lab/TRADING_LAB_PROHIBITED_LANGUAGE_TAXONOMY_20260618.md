# Trading Lab Prohibited Language Taxonomy

Date: 2026-06-18

## Purpose

This taxonomy defines language that should be rejected or held for manual
review in Trading Lab artifacts. Trading Lab remains paper-only, research-only,
and not investment advice.

| category | prohibited_examples | safe_rewrites | expected_validation_behavior | HOLD vs REJECT notes |
| --- | --- | --- | --- | --- |
| execution commands | `place order`, `submit order`, `execute` | `manual review`, `paper-only observation` | REJECT | REJECT when the text implies action or order flow. |
| broker/API references | `broker API`, `connect broker`, `order endpoint` | `public source review`, `manual citation` | REJECT | HOLD only if discussing why broker/API is prohibited in policy docs. |
| credential/secret/key/token references | `API key`, `broker token`, `secret key`, `Bearer ...` | `no credentials required`, `public source only` | REJECT | REJECT if presented as usable config or source dependency. |
| private account data references | `brokerage balance`, `account holdings`, `private brokerage export` | `fixed fictional paper unit`, `public-source note` | REJECT | HOLD only for policy language explaining prohibition. |
| production advice language | `buy now`, `sell now`, `for your account` | `research question`, `paper-only hypothesis` | REJECT | REJECT when directed at a real account or action. |
| guaranteed-return language | `guaranteed return`, `risk-free profit` | `hypothesis uncertainty`, `risk note` | REJECT | REJECT as advice/claim language. |
| automated-trigger language | `auto-execute`, `automated trigger`, `trigger order` | `manual review if observed` | REJECT | REJECT if automation is implied. |
| data-ingestion language | `data ingestion`, `ingest market data` | `future proposal requires gate`, `manual review only` | REJECT in artifacts | HOLD in gate docs only when describing blocked future work. |
| generated-output language | `generated outputs`, `generated market dataset`, `promote generated artifacts` | `no generated output`, `docs-only review` | REJECT in artifacts | HOLD in policy docs only when explaining future gate requirements. |

## Safe Use Reminder

Policy and gate docs may mention prohibited phrases to define guardrails. Actual
research artifacts must reject those phrases when they imply behavior,
configuration, data flow, advice, or execution.

## T17 Rewrite Lock

Use `TRADING_LAB_SAFE_REWRITE_LIBRARY_20260618.md` when replacing unsafe
language. Safe rewrites must use research questions, manual review, public
evidence, paper-only hypotheses, risk notes, and invalidation conditions.

No rewrite may preserve broker/API, credential, secret, key, token, private
account, order, execution, automation, guaranteed-return, or production-advice
meaning.
