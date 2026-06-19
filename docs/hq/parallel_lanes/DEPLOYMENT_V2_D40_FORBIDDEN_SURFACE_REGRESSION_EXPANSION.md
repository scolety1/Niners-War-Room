# Deployment V2 D40 Forbidden Surface Regression Expansion

## Scope

This document records expanded inert regression coverage for the Deployment V2
local-only surface guard. It does not approve hosted deployment, create deploy
commands, add CI/CD, create containers/images, expose public ports, create
secrets, route production traffic, define hosted smoke plans, or change
app/runtime behavior.

## Expanded Coverage

The guard now has temp-fixture coverage for additional command-surface markers:

- public port hints
- hosted route hints
- hosted smoke hints

These checks are limited to command-surface files such as Makefile, Taskfile,
package, pyproject, and tox surfaces. Normal docs can still describe these
concepts as blocked without creating false positives.

## Fixture Safety

All added test fixtures are temporary and inert.

No real deploy config files, public routes, hosted smoke plans, secrets,
credentials, containers, or CI/CD workflows were added to the repository.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
