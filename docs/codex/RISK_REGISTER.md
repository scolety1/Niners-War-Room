# Risk Register

## Risk Summary

Primary risks are wrong league-rule interpretation, bad CSV imports, hidden dependency creep, accidental runtime API reliance, and overbuilding UI before model correctness.

## Approval Gates

- Package/dependency changes require dependency approval.
- Runtime API collectors require external-services approval.
- SQLite schema changes require migration proposal and approval.
- Auth, payment, deploy, secrets, and production data work are out of scope.
- Complex ML is out of scope for V1.

## Sensitive Systems

No sensitive systems are used in V1. No auth, payments, production APIs, secrets, customer data, or deployment targets are configured.

## Mitigations

- Keep runtime local-first and snapshot-based.
- Validate imports before writing accepted data.
- Store import errors and warnings.
- Test every formula.
- Keep official rank separate from market/private strategy values.

## Open Risks

- Source roster packet may need manual cleanup before CSV import.
- Rulebook edge cases around shield trades and Roster Declaration Day may require configuration updates.
- Market values may be incomplete until the user supplies cleaned snapshots.
