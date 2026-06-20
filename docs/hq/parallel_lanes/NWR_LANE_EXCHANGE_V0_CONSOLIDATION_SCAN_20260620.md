# NWR Lane Exchange V0 Consolidation Scan

Date: 2026-06-20

Owner: Master/Main HQ

## Scope

This checkpoint records the Lane Exchange V0 registry path consolidation and the
known lane implementation commits. It does not create real exchange packages,
copy data, run simulations, deploy, or reopen Drop Decision.

## Registry Path Decision

Official Lane Exchange hub root:

```text
C:\NWR_SHARED_DATA\lane_exchange\
```

Official Lane Exchange V0 registry path:

```text
C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json
```

This registry is local-only and outside Git. It is the operational ownership
index for Lane Exchange V0. The Master contract remains the source of truth.

Registry paths checked:

| Path | Status |
| --- | --- |
| `C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json` | exists; official |
| `C:\NWR_SHARED_DATA\lane_exchange\lane_exchange_registry\lane_exchange_v0_registry.json` | missing; not official |
| `C:\NWR_SHARED_DATA\lane_exchange\registry\lane_exchange_v0_registry.json` | missing; not official |
| `C:\NWR_SHARED_DATA\lane_exchange\lane_exchange_v0_registry.json` | missing; not official |

No duplicate or stale wrong-path registry was found during this scan.

## Known Lane Exchange Implementation Board

| Lane | Status | Known implementation commit | Notes |
| --- | --- | --- | --- |
| Master/Main | GREEN | `180134d Document NWR lane exchange v0 contract` | Owns contract and local registry path decision. |
| Mock Draft | GREEN | `e5a2511 Add mock draft lane exchange readiness validator` | Consumer/validator for required draft-day packages. |
| Rookie HQ | GREEN | `6573ffb Add rookie lane exchange publisher capability` | Producer for `rookie_hq/frozen_rookie_mock_input`. |
| Outcome V1 | GREEN | `f703963 Add outcome lane exchange capability` | May publish only explicitly approved display/output snapshots. |
| Deployment V2 | GREEN | `56f3a62 Add deployment v2 lane exchange awareness guard` | Awareness guard only; no deploy approval. |
| Trading Lab | GREEN | `5fcfec3 Add trading lab lane exchange capability` | Research snapshot capability only; no broker/API/trading use. |
| QA/Data Hygiene | HOLD | none | No safe repo/worktree; remains inactive. |
| Drop Decision | HOLD/FROZEN | none | Do not touch. Any exchange data must come from already-approved/frozen outputs only. |

## Consolidation Notes

- The official registry path is readable at
  `C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json`.
- The local-only hub README was updated to warn that registries nested under
  `C:\NWR_SHARED_DATA\lane_exchange\` are not official.
- No real data, `local_exports`, package snapshots, generated artifacts, caches,
  or secrets were copied into Master or the exchange.
- No lane worktree outside Master/Main was modified by this checkpoint.
- No deployment, simulation, app wiring, or production data import was performed.

## Remaining Gates

- First pinned live snapshot still requires explicit Master/Tim approval.
- Required Mock Draft real input packages still require approved package
  snapshots before live draft use.
- Market/ADP packages remain optional and display-only. They must never become
  NWR private value.
