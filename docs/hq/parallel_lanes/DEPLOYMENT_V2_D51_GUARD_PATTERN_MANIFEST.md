# Deployment V2 D51 Guard Pattern Manifest

## Scope

This manifest maps forbidden-surface categories to guard and test coverage. It
is documentation only. It does not approve hosted deployment, create deploy
commands, add CI/CD, create containers/images, expose public ports, create
secrets, route production traffic, create zip exports, or change app/runtime
behavior.

## Coverage Map

| Category | Guard coverage | Test coverage |
|---|---|---|
| Deploy command surfaces | command-surface pattern checks | `test_guard_flags_container_manifest_and_deploy_command` |
| CI/CD workflow-like surfaces | `.github/workflows` path detection | `test_guard_flags_ci_workflow_in_temp_fixture` |
| Containers/images | manifest names such as Dockerfile/Containerfile/compose | temp manifest fixture tests |
| Public ports/routing | command-surface patterns for public port and hosted route hints | D40 command-surface tests |
| Secrets/credentials | blocked by policy/docs; no secret-shaped fixtures are used | handoff/artifact docs and transcript checks |
| Hosted smoke plans | command-surface hosted smoke marker | D40 hosted smoke test |
| Hosted platform config names | platform manifests such as render, fly, railway, vercel, netlify | temp manifest fixture tests |
| Production runtime language | docs audit hosted-readiness language checks | docs consistency audit tests |
| Generated/data/local-only paths | skipped directories plus artifact exclusion docs | skipped-dir guard test and D33 audit guide |

## Safe Fixture Rule

Guard tests use temporary directories only. They must not add real deploy
configuration files, secrets, credentials, containers, public routes, hosted
smoke plans, or generated artifacts to the repository.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.
