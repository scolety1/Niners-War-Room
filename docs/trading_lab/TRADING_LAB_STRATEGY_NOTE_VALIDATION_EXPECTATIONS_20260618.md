# Trading Lab Strategy Note Validation Expectations

Date: 2026-06-18

## Purpose

Strategy notes are research-only structures for hypotheses, assumptions, public
evidence, paper-test design, invalidation conditions, and review cadence. They
are not trading signals or investment advice.

## Acceptable Content

Safe strategy notes may include:

- Hypothesis
- Assumptions
- Public evidence or source names
- Paper-test design
- Invalidation conditions
- Review cadence
- Known limitations
- Research-only notes

## Prohibited Content

Reject strategy notes that include:

- `buy now` or `sell now`
- Broker/order instructions
- Account-balance-dependent decisions
- Automated triggers
- Secret, token, key, or credential references
- Private brokerage data
- Deployment or app wiring plans

## Validation Examples

| example | expected_result | why |
| --- | --- | --- |
| Study how a simple rule behaves in a future paper simulation | ACCEPT | Research question only; no code or execution. |
| Compare public earnings calendar references for event-study design | ACCEPT | Public-source paper design. |
| Review public macro series as descriptive context | ACCEPT | Research-only context. |
| `Buy EXMPL now` | REJECT | Investment advice and real-money instruction. |
| `Send broker order after confirmation` | REJECT | Broker/order workflow. |
| `Use account balance for sizing` | REJECT | Private account data dependency. |
| `Auto-execute when signal crosses threshold` | REJECT | Automated execution trigger. |
| `Store API token for source access` | REJECT | Secret/credential reference. |

## Safe Use Reminder

Strategy notes may define research questions for later paper review. They must
not become trading recommendations, execution rules, broker workflows, private
account decisions, generated outputs, or deployment plans.
