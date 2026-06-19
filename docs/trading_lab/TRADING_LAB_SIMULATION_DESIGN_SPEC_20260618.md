# Trading Lab Simulation Design Spec

Date: 2026-06-18

## Status

Future scope only. Not approved for implementation.

## Prohibitions

- No data ingestion.
- No market-data fetching.
- No generated outputs.
- No broker/API integration.
- No credentials, secrets, keys, or tokens.
- No real-money execution.
- No automated execution.
- No app wiring.
- No deployment.
- No investment advice.

## Future Public-Only Data Requirements

Any later proposal would need separate approval and must define:

- Public source inventory.
- License/terms review.
- Attribution requirements.
- Storage policy.
- Refresh cadence.
- Generated artifact policy.
- Validation plan.

## Design Questions For A Later Phase

- What question is the paper simulation trying to study?
- What public sources would be allowed?
- What survivorship, lookahead, and selection biases must be controlled?
- What benchmark assumptions are appropriate?
- What transaction-cost assumptions are documented?
- What slippage assumptions are documented?
- How are paper results labeled as non-advice?
- What closeout proves no execution path exists?

## Validation Expectations For A Later Proposal

- Explicit user/Master approval.
- Source policy gate completed.
- No secrets or private account data.
- No broker/API objects.
- No app/deployment changes.
- No generated outputs unless separately approved.
- Focused tests for validation-only guardrails.

## Closeout Requirements For A Later Proposal

- Files changed.
- Validation run.
- Guardrails preserved.
- Generated artifact policy.
- Ready/blocked list.
- Explicit statement that paper simulation is not investment advice.
