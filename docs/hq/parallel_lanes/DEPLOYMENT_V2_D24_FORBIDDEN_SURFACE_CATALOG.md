# Deployment V2 D24 Forbidden Surface Catalog

## Scope

This catalog defines forbidden Deployment V2 surfaces for discovery validation.
It is not a deployment plan and does not approve hosted deployment, create
deploy commands, add CI/CD, create containers/images, expose public ports,
create secrets, route production traffic, or change app/runtime behavior.

Use this catalog to keep future guard changes precise and conservative.

## Forbidden Surface Categories

### Deploy Commands

Blocked because no Deployment V2 deploy command is approved.

Includes command surfaces that would publish, upload, release, route, package,
or run the app outside the local-only operator flow.

If detected: stop and mark RED unless HQ explicitly approved the exact command
in a future hosted-deployment sprint.

### CI/CD Deploy Workflows

Blocked because automated deployment policy is unapproved.

Includes workflow files, protected environment references, deploy-on-push
automation, release jobs, and platform token usage.

If detected: stop and mark RED.

### Containers And Images

Blocked because container/image policy is unapproved.

Includes container manifests, image build files, compose manifests, image
registry references, and orchestration manifests.

If detected: stop and mark RED.

### Public Ports And Routing

Blocked because public/private access policy and hosted routing policy are
unapproved.

Includes public tunnel references, hosted route configuration, external share
URLs, public app exposure, and reverse-proxy routing.

If detected: stop and mark RED.

### Secrets And Credentials

Blocked because secrets policy is unapproved.

Includes credentials, tokens, secret-manager configuration, environment files,
private keys, service accounts, and credential-shaped values.

If detected: stop and mark RED. Do not print secret values in reports.

### Hosted Smoke Plans

Blocked because hosted deployment itself is blocked.

Includes test plans or runbooks that assume a hosted target, public route,
external health endpoint, hosted smoke URL, or platform release identifier.

If detected: mark YELLOW or RED depending on whether it is speculative text or
an actionable hosted workflow. Do not execute.

### Production Runtime Changes

Blocked because Deployment V2 discovery is not allowed to alter production app
behavior.

Includes app UI wiring, runtime configuration changes, data-pack routing,
Outcome behavior changes, hidden sort keys, promoted artifacts, or operator
path behavior changes outside docs.

If detected: stop and mark RED.

## Allowed Discovery Surfaces

Allowed surfaces remain limited to:

- Deployment V2 docs under `docs/hq/parallel_lanes/`
- read-only validation scripts under `scripts/`
- matching tests under `tests/`
- existing local-only guard files when needed

Allowed surfaces must remain read-only and local-only. They must not introduce
deploy infrastructure or app/runtime behavior.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command exists.

No CI/CD workflow, container/image, public route, public tunnel, secret,
credential, hosted smoke plan, or production runtime behavior is approved.
