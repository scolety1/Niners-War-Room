# Deployment V2 D66 Guard False-Positive Review

This guide helps operators distinguish safe local-only documentation from forbidden deploy-surface language.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Safe Documentation Language

Safe docs may state:

- hosted deployment remains blocked
- deployment surfaces are forbidden in this lane
- local-only validation passed
- a blocked surface example is non-executable documentation
- a historical path appears only as a historical note
- a future hosted lane would require separate approval

Safe docs must not introduce runnable platform instructions, credential creation, public routing steps, CI/CD setup, containers/images, app launch instructions, or hosted smoke procedures.

## Forbidden Guard Surface Language

The local-only guard should flag forbidden surfaces when they appear in executable or command-oriented files such as `Makefile`, `package.json`, `pyproject.toml`, `Taskfile.yml`, or `tox.ini`.

Forbidden categories include:

- deploy command surfaces
- CI/CD workflow-like surfaces
- containers/images
- public ports/routing
- secrets/credentials
- hosted smoke plans
- hosted platform config names
- production runtime changes
- generated/data/local-only artifact paths

## Review Steps

1. Confirm the finding path.
2. If the path is a docs file, verify whether the language is explicitly blocked, forbidden, historical, or conditional.
3. If the path is a command-surface file, treat deploy-oriented wording as RED unless it is clearly a temporary test fixture.
4. Do not weaken the guard to make a real forbidden surface pass.
5. If a false positive exists, add a focused temp-fixture test before changing the guard.

## Reporting

False-positive review can return GREEN only when:

- the real repository has no deploy surface
- docs audit is GREEN or GREEN with historical-path NOTE only
- readiness runner is GREEN after allowed changes are committed
- hosted deployment remains BLOCKED
