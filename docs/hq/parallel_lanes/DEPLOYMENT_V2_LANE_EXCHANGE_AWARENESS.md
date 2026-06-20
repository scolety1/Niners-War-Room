# Deployment V2 Lane Exchange Awareness

## Purpose

Deployment V2 can report local Lane Exchange readiness by reading the Master Lane Exchange V0 contract and the local-only registry.

This is visibility and validation only. It does not deploy, create deploy commands, add CI/CD, create containers/images, expose public ports, create secrets, create zip/export artifacts, wire app runtime behavior, or make hosted deployment ready.

## Source Of Truth

Master contract:

```text
C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_LANE_EXCHANGE_V0_CONTRACT.md
```

Local-only registry:

```text
C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json
```

Local-only exchange hub:

```text
C:\NWR_SHARED_DATA\lane_exchange
```

The Master contract remains the source of truth. The registry is read as an operational index only.

## Deployment V2 Role

Deployment V2 is an exchange observer for readiness reporting.

Allowed:

- confirm the contract is readable
- confirm the registry is readable
- confirm the hub path is local-only and outside Git repos
- confirm registry rules mark exchange snapshots as do-not-commit
- report GREEN/YELLOW/RED readiness

Blocked:

- publishing exchange snapshots
- committing exchange snapshots or registry data
- copying exchange data into this repo
- making hosted runtime depend on the exchange hub
- creating deploy, CI/CD, container, public routing, or hosted smoke behavior
- changing app/runtime behavior

## Validation Command

```powershell
python scripts/validate_lane_exchange_local_only.py
```

Optional machine-readable output:

```powershell
python scripts/validate_lane_exchange_local_only.py --json
```

## Expected GREEN Meaning

GREEN means Deployment V2 can see the local contract/registry/hub boundary and can report that exchange data remains local-only and outside Git packaging.

GREEN does not mean hosted deployment is ready. Hosted deployment remains BLOCKED pending hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan.

## Data Boundary

No real exchange snapshots, manifests, generated files, archives, registry files, or `C:\NWR_SHARED_DATA` contents are committed to this repo. Tests use temporary fake data only.

V1 remains `local_only`. No deploy command exists. Deployment V2 is not the operator app path.
