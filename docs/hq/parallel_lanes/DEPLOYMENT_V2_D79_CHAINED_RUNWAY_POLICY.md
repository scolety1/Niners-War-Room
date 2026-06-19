# Deployment V2 D79 Chained Runway Policy

This policy defines how Deployment V2 may chain multiple safe runways without losing the local-only posture.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Acceptable Chained Work

Chained work may include:

- Deployment V2 docs clarity
- read-only validation scripts
- matching tests using temp fixtures
- validation report schema improvements
- operator handoff/reporting templates
- guard hardening that does not weaken existing protection

## Max Scope Per Chain

A chain should stay within one coherent validation/docs theme and avoid mixing unrelated app behavior. A good chain contains 5-10 tasks. Larger chains must have explicit task-by-task validation and one commit per completed task.

## Hard Stop Conditions

Stop immediately for:

- wrong branch
- dirty repo before work
- baseline missing from current history
- failed guard that cannot be fixed within Deployment V2 docs/scripts/tests
- request for hosted deployment work
- request for a deploy command
- request to add CI/CD or containers/images
- request to create secrets/credentials
- request to expose public ports or routing
- request to touch Outcome/Rookie/Mock Draft/Drop Decision/Trading Lab/QA/Data Hygiene/Master behavior
- request to commit data/generated/local-only artifacts

## YELLOW Conditions

Return YELLOW when:

- optional import zip is missing
- Python validation is unavailable but docs-only work is safe
- historical path notes remain but current desktop-era docs are correct
- schema/report output is parseable but an optional check is skipped

## BLOCKED Hosted Posture

Hosted blockers remain BLOCKED, not YELLOW, until the user explicitly approves:

- hosted target
- owner
- secrets policy
- data policy
- access policy
- rollback policy
- deploy command policy
- CI/CD policy
- public/private routing policy
- hosted smoke plan

## Zip/Export Policy

Do not create zip exports by default. Use only provided import verification zips unless the user explicitly approves creating a new export artifact.

## Final Claim

A chained runway can claim GREEN only when the worktree is clean, safe validations pass, no deploy surface was added, no zip/export was created, no other lane was touched, and hosted deployment remains BLOCKED.
