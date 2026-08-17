# Current NWR State

Audit date: 2026-08-17. All checks were read-only except creation of this docs-only branch.

| State | Path / ref | Branch | HEAD | Clean | Finding |
|---|---|---|---|---|---|
| Trusted remote-backed repository | `C:\NWR\Niners-War-Room-V1` | `work/hq-parallel-control` | `dec9e18dcb41d252723759a950b33b5ca5e4b2d7` | yes | Current fetched HQ; does not contain the later desktop reconciliation chain. |
| Audit worktree | `C:\Users\codex-agent\Documents\Niners War Room\.nwr-complete-audit-worktree` | `audit/nwr-complete-capability-external-adoption-v1-20260817` | based on `dec9e18...` | yes before packet | Isolated docs lane. |
| Strongest clean local candidate | `C:\NWR\nwr-desktop-owner-reconciliation-v1-20260814` | `codex/nwr-desktop-owner-reconciliation-v1-20260814` | `9cb6eaf5eb370c69c5732aea8ced9419783b10b5` | yes | Exact 18-commit descendant of HQ; 286-file desktop/product reconciliation. |
| Installed Dynasty | `%LOCALAPPDATA%\Niners War Room — Dynasty` | binary | sidecar SHA-256 `4B7F4866F829314F7B2DE40CD3EF32F2D8C39E4A62D9C838C42CD465A13FA60B` | n/a | Pre-Redraft reconciliation build. Exact commit receipt is missing; functionally aligns with the Dynasty reconciliation lineage. |
| Installed Redraft | `%LOCALAPPDATA%\Niners War Room — Redraft` | binary | sidecar SHA-256 `592A5DBECE1A232A19083E995D0B039B864337B06C7C292CC00A4B16759A10B2` | n/a | Exact hash match to the build under the `9cb6eaf...` worktree. |

Remote: `origin` = `https://github.com/scolety1/Niners-War-Room.git`. Fetched remote HQ HEAD was `dec9e18...` at recovery time.

## Candidate lineage

`9cb6eaf...` descends directly from HQ and adds, in order, the packaged desktop experience, installed trust fixes, decision semantics, plausibility/outlier closure, rookie eligibility/intelligence, Sleeper Redraft owner import, K/DST external-consensus boundary, practical mock mode, rookie-veteran multi-authority compare and isolated Redraft league workspaces. Its merge base with HQ is exactly `dec9e18...`; this is not an unrelated history.

## Installed state

Dynasty and Redraft use distinct application and LocalAppData roots (`com.ninerswarroom.dynasty` and `com.ninerswarroom.redraft`). Owner data is local, lock-protected and atomically written with backup/restore support. Nothing in this audit modified either installed root.

## Governing plan

The supplied governing plan SHA-256 was independently verified as `83630daf365aa042392955837135ad3f3d5a62cf8434fd58adf5f38c08b23f78`. This packet follows its local-first, explicit-authority, no-silent-model-change, read-only Sleeper and no-mandatory-paid-provider boundaries. Proposed clarifications are isolated in `GOVERNING_PLAN_CHANGE_REQUESTS.md`.

## Recovery conclusion

HQ is clean and trustworthy but behind. `9cb6eaf...` is the strongest overall source candidate and the exact Redraft installed source authority. Owner adoption must reconcile that chain before new implementation. This audit does not merge or promote it.
