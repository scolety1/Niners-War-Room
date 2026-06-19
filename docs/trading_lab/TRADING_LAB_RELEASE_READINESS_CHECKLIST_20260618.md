# Trading Lab Release Readiness Checklist

Date: 2026-06-18

## Source Inventory Validators

- [ ] Required metadata fields are present.
- [ ] Source category is allowed.
- [ ] Intended use is paper/research-only.
- [ ] Broker, credential, private-account, and execution terms are rejected.
- [ ] Config fields reject secret-like names and values.

## Artifact Validators

- [ ] Manual artifact required fields are checked.
- [ ] Unsupported artifact types are rejected.
- [ ] Nested manual review packet text is inspected.
- [ ] Paper journals reject execution and private-account wording.
- [ ] Watchlist notes require paper-only status and public sources.

## Schema Registry

- [ ] Supported artifact types are listed.
- [ ] Required fields are documented.
- [ ] Allowed statuses are explicit.
- [ ] Prohibited field names are blocked.

## Blocked-Work Gate

- [ ] Research-only maintenance is allowed.
- [ ] Data ingestion, generated outputs, deployment, and backtesting proposals
  are held for explicit approval.
- [ ] Broker/API, credentials, private-account data, execution, advice, and
  fantasy-lane drift are rejected.

## No-Advice Tests

- [ ] Buy-now and sell-now language is rejected.
- [ ] Guaranteed-return language is rejected.
- [ ] Safe research-question rewrites are accepted.
- [ ] Paper-only manual review wording remains accepted.

## Release Handoff Docs

- [ ] Master handoff packet exists.
- [ ] Chain closeout exists.
- [ ] Ready and blocked lists are current.
- [ ] Validation commands are included.
