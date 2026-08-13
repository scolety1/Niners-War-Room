# NWR Desktop Experience V1 — Architecture

## Product boundary

Desktop V1 ships two owner applications. They do not expose an owner-facing mode switch.

| Product | Windows identity | Frontend | Local API mode | Mutable state |
|---|---|---|---|---|
| Niners War Room — Dynasty | `com.ninerswarroom.dynasty` | `desktop/apps/dynasty` | `dynasty` | Dynasty-only LocalAppData namespace |
| Niners War Room — Redraft | `com.ninerswarroom.redraft` | `desktop/apps/redraft` | `redraft` | Redraft-only LocalAppData namespace |

The applications share visual primitives, TypeScript contracts, the local client, the Rust lifecycle host, player identity, and existing Python analytical services. They do not share navigation, active league context, draft state, or owner-facing entrypoints.

## Runtime

```text
Existing governed Python services and frozen data
                    |
          framework-neutral facade
                    |
 launch-authenticated, ephemeral loopback-only JSON contract v1
                    |
        shared TypeScript desktop client
                    |
       Dynasty React app | Redraft React app
                    |
       distinct Tauri 2 Windows executables
```

Python remains the analytical authority. React does not recalculate rankings, market gaps, rookie review, Outcome V3, trade dimensions, Redraft scoring, replacement levels, or draft-board persistence.

The adapter uses Python's standard-library threaded HTTP server instead of adding a web-framework dependency. This is the permitted “FastAPI or equivalent thin adapter” architecture: the contract is local, typed, bounded, and independently tested while retaining the repository's offline-first dependency posture.

## Preserved authorities

Dynasty composes the existing Finished V1 rankings, governed asset registry, unified research preview, Outcome V3 display bundle, Rookie Review, Player Compare, Trade Decision Assistant, and Personal Workspace summary. Market information remains display-only.

Redraft delegates profiles, scoring, projection admission, replacement-level rankings, tiers, draft marking, undo, and atomic persistence to `redraft_engine_v1_service.py`. Its committed 608-player current-season snapshot is installed through the existing approval validator only when a new Redraft state root has no projection. Existing local projections are never overwritten by first-run seeding.

## Desktop lifecycle

Each Tauri executable launches a fixed mode. The Rust host:

1. resolves immutable bundled resources and a mode-specific LocalAppData state root;
2. generates distinct cryptographically random API and startup-proof secrets for the launch;
3. starts the exact frozen Python child, assigns it to a kill-on-close Windows Job Object, and delivers both secrets once through inherited standard input; never through arguments or environment;
4. has Python atomically bind an OS-assigned high port on `127.0.0.1`, retain that listener, and announce a bounded startup record through inherited standard output;
5. verifies the announced listener PID belongs to the Job Object and resolves to the exact frozen sidecar image;
6. verifies a fresh HMAC-SHA256 proof bound to protocol, mode, port, and host challenge before transmitting the API bearer;
7. authenticates exact-mode `/healthz`, re-verifies listener ownership and child liveness, and only then reveals the window;
8. exposes only the matching launch-bound runtime descriptor to the matching WebView;
9. stops only its exact child/job when the app exits.

Release builds fail closed if the self-contained sidecar is absent. Development builds may use an explicitly configured Python interpreter and source entrypoint.

## Security boundary

- No bind to `0.0.0.0`, hostname wildcard, or external interface.
- Production secrets are cryptographically random for every launch and have no environment override.
- Launch secrets are delivered once over inherited standard input and are absent from child arguments, child environment, persisted runtime state, and lifecycle logs.
- Readiness requires an HMAC-SHA256 possession proof over a fresh host challenge; the browser-visible API bearer is never sent to an unproved listener.
- Exact mode-scoped CORS origins; no wildcard origin.
- 256 KiB JSON body limit and 4 KiB request-target limit.
- Unknown request fields, query strings, unsupported methods, and wrong-mode routes fail closed.
- Cross-mode endpoints return `404`.
- Responses are no-store and redact filesystem paths from public DTOs.
- Tauri capabilities expose only the launch-bound runtime descriptor and exact window-chrome commands to that app's main window.
- No shell, generic filesystem, external HTTP, updater, telemetry, CDN, provider API, or cloud dependency is exposed to the frontend.
- Bundles exclude `local_exports`, caches, credentials, and owner state.

## Legacy rollback

Streamlit remains unchanged as the legacy/fallback/development UI. Desktop V1 is additive. No Streamlit page, launcher, analytical service, or governed pack is deleted by this migration.
