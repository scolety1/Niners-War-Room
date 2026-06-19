# Deployment V2 D17 Discovery Guardrail Validation

## Scope

This document records a discovery-only validation improvement for Deployment V2.
It does not approve hosted deployment, create deployment infrastructure, add
CI/CD, add containers, expose public ports, create secrets, wire app UI, or
change production runtime behavior.

## Added Guard

Deployment V2 now has a read-only local-only surface guard:

```powershell
python scripts\validate_local_only_surface_guard.py
```

The guard scans the repository for accidental hosted deployment surfaces:

- CI/CD workflow files under `.github/workflows`
- container manifests such as `Dockerfile`, `Containerfile`, and compose files
- hosted platform manifests such as `fly.toml`, `render.yaml`, `railway.toml`,
  `vercel.json`, and `netlify.toml`
- Kubernetes or Helm path segments
- deploy-oriented command entries in package, Makefile, pyproject, tox, and
  Taskfile command surfaces
- public tunnel command references such as `ngrok`, `cloudflared tunnel`, or
  `localtunnel`

The guard intentionally allows the documented local operator command:

```powershell
streamlit run app/main.py
```

That command is local operation only and is not a hosted deployment command.

## Pytest Coverage

Focused pytest coverage confirms:

- the current repository has no detected deploy surface
- the local Streamlit operator command is not treated as deployment
- a container manifest and package deploy script are blocked

## Current Posture

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command exists.

No CI/CD deploy workflow, container, hosted platform manifest, public tunnel, or
production routing path was added.

## Future Use

Future Deployment V2 agents should run the guard during discovery validation,
especially before claiming that hosted deployment remains blocked and no deploy
surface exists.
