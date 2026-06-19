# Trading Lab Placeholder Integration Boundary Map - 2026-06-18

This map documents what the fake-data Trade Lab UI can show now and what future work would require. It does not approve any integration work.

## Current Fake/In-Memory Areas

| Area | Current Status | Boundary |
|---|---|---|
| NWR private value | Placeholder only | Not wired; needs explicit approval before integration |
| Public fantasy market value | Placeholder only | Not wired; needs explicit approval before integration |
| Roster context | Placeholder only | Not wired; needs explicit approval before integration |
| Drop pressure | Placeholder only | Not wired; needs explicit approval before integration |
| Rookie board context | Placeholder only | Not wired; needs explicit approval before integration |
| Mock draft context | Placeholder only | Not wired; needs explicit approval before integration |
| Training Mode | Fake scenarios only | No real data and no automatic choices |

## Future Integration Placeholders

- Future NWR private value integration must be read-only and explicitly approved.
- Future public fantasy market value integration must be read-only and explicitly approved.
- Future roster context integration must be read-only and explicitly approved.
- Future drop pressure integration must be read-only and explicitly approved.
- Future rookie/mock draft context integration must be read-only and explicitly approved.

## Required Explicit Approvals

Before any future integration can be proposed, the phase prompt must explicitly approve the specific source, path, read/write behavior, validation expectations, and rollback plan.

## Forbidden Integrations

- Stock-market, broker, crypto, equity, or real-money finance integrations.
- Credentials, secrets, keys, tokens, or private account data.
- Generated outputs.
- Automated trade submission.
- Automatic fantasy trade decisioning.
- Deployment.

## Current Verdict

GREEN for fake-data review. HOLD for all real integrations.
