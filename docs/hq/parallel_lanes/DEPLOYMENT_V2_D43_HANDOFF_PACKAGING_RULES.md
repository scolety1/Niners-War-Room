# Deployment V2 D43 Handoff Packaging Rules

## Scope

This policy defines what Deployment V2 may hand off in future reports. It is
documentation only. It does not create zip exports, approve hosted deployment,
create deploy commands, add CI/CD, create containers/images, expose public
ports, create secrets, route production traffic, define hosted smoke plans, or
change app/runtime behavior.

## Default Rule

Deployment V2 does not create generated handoff packages by default.

Source, data, export, archive, and generated artifact contents must not be
bundled unless explicitly approved in a later task.

Generated zip exports are not default.

## Safe Handoff Content

Safe handoff content includes:

- commit hashes
- changed file lists
- validation outputs
- docs paths
- script names
- focused test names
- local-only guard results
- readiness runner results
- docs consistency results
- transcript printer results
- GREEN/YELLOW/RED verdicts

These may be reported as text in the final response or in approved docs under
`docs/hq/parallel_lanes/`.

## Blocked Handoff Content

Blocked handoff content includes:

- secrets
- credentials
- private keys
- service account files
- `.env`
- `data/`
- `local_exports/`
- generated artifacts
- app runtime outputs
- deploy configs
- hosted credentials
- source/data/export/archive bundles
- generated zip exports, unless explicitly approved

## Reporting Existing Artifacts

If a future audit notices existing tracked generated artifacts, report them as
outside-lane notes unless the user explicitly approves a cleanup lane.

Do not clean, package, export, or rewrite artifacts from Deployment V2 without
specific approval.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
