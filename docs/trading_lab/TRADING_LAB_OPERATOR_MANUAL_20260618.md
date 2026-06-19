# Trading Lab Operator Manual

Date: 2026-06-18

## Purpose

This manual describes the manual Trading Lab workflow from research intake to
closeout. Trading Lab is paper-only, research-only, and not investment advice.
It is not a broker/API, execution, data ingestion, deployment, generated-output,
or fantasy-football lane.

## Manual Workflow

1. Source review: confirm a source is public, citeable, non-secret, and
   research-only.
2. Research note intake: capture the research question before drafting any
   watchlist or journal note.
3. Watchlist note drafting: write a paper-only note with public source names,
   risks, and invalidation notes.
4. Risk review: record thesis, data-quality, bias, process, and
   execution-policy risks.
5. Paper journal entry: record a hypothetical paper-only observation and review
   date.
6. Review/closeout: check guardrails, review lessons, and close or hold the
   paper note.

## Operators May Do

- Write public-source research notes.
- Draft fake/public-only examples.
- Record paper-only hypotheses.
- Review source attribution and terms.
- Mark notes as HOLD or REJECTED when guardrails are unclear.
- Capture lessons learned without making recommendations.

## Operators May Not Do

- Place or route broker orders.
- Connect broker APIs.
- Store credentials, secrets, keys, tokens, cookies, or `.env` files.
- Use private brokerage/account data.
- Create data ingestion jobs or generated market datasets.
- Add automated execution.
- Give production investment advice.
- Deploy anything or wire app behavior.
- Touch fantasy-football lanes or inherited app behavior.

## Guardrail Checklist

- Paper-only status is explicit.
- Research question is neutral.
- Public sources are cited or source review is marked HOLD.
- No private account data appears.
- No credential or secret appears.
- No broker/API dependency appears.
- No execution path appears.
- No advice language appears.
- Risks and invalidation conditions are documented.
- Closeout status is recorded.

## Stop And Escalate

Stop and escalate if a request mentions or requires:

- Credentials, secrets, keys, tokens, or `.env`
- Broker APIs, order endpoints, order routing, or execution
- Private account data, balances, holdings, fills, or exports
- Data ingestion, generated datasets, or generated outputs
- Deployment or app wiring
- Fantasy-lane files or behavior
- Buy/sell/hold advice for a real account

## Safe Closeout

Every manual workflow should end with one of these statuses:

- `CLOSED_LESSONS`
- `HOLD_NEEDS_REVIEW`
- `REJECTED_PROHIBITED`

No status represents an order, signal, recommendation, or execution workflow.
