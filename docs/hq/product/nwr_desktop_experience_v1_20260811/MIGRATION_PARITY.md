# NWR Desktop Experience V1 — Migration and Parity

## Strangler migration

Desktop V1 is an additive presentation and lifecycle layer over the existing backend. It does not replace analytical formulas, data governance, or persistence services.

| Existing capability | Desktop surface | Reuse strategy | V1 authority |
|---|---|---|---|
| Finished V1 dynasty rankings | Dynasty Home / Rankings | Direct governed loader and owner evidence composition | Finished V1 |
| Market baseline | Dynasty Market / Player Detail | Display-only fields from owner evidence | Context only |
| Rookie Review | Dynasty Rookie Intelligence | Existing owner rookie-board loader | Review authority |
| Outcome V3 | Dynasty Player Detail / Compare | Existing display and player-matrix services | Display only |
| Player Compare | Dynasty Compare | Existing universe and owner summary | Source separated |
| Trade Decision Assistant | Dynasty Trade Lab | Existing ordinal decision evaluator | Decision authority |
| Personal Workspace | Dynasty My Board / Decision Tracker / Planning | Existing atomic, checksummed board, journal, scenario, backup, restore-preview, and create-only legacy adoption services | Owner-local |
| Dynasty live draft runtime | Dynasty Draft Cockpit | Read-only evidence, player detail, and comparison surface; Streamlit retains live session writes for V1 | Legacy runtime authority |
| Redraft profiles and scoring | Redraft Profile & Scoring | Existing validated profile store | Redraft V1 |
| Redraft rankings and tiers | Redraft Draft Room / Rankings / Tiers | Existing scoring and replacement engine | Redraft V1 |
| Redraft draft state | Redraft Draft Room | Existing atomic ordered-ID board and undo | Owner-local |
| Data health | Both applications | Mode-specific composed health DTO | Fail closed |

## State rules

- Immutable governed resources are bundled read-only.
- Dynasty and Redraft mutable roots are mode scoped under LocalAppData.
- First-run Redraft projection seeding is create-only; it never overwrites an installed snapshot.
- Streamlit continues to use its established paths until owner acceptance authorizes a later deprecation.
- An empty Desktop workspace can explicitly adopt the established Streamlit workspace. Adoption creates and validates a source backup, requires confirmation, refuses a non-empty destination, and never mutates or overwrites the source.
- No legacy source is deleted during Desktop V1.
- Dynasty Planning writes only manual checkpoints and notes. Stable per-module scenario IDs preserve one current record per planning module and never alter ranks, projections, or source data.
- Dynasty live draft mutation remains in Streamlit until the desktop adapter can preserve the existing runtime's session lifecycle, event log, source checkpoint, backup, import, and recovery semantics together.

## Explicit non-goals

- Rewriting Python models or formulas in TypeScript or Rust.
- Cloud hosting, remote authentication, telemetry, or provider calls.
- Combining Dynasty and Redraft into one mode-switching owner application.
- Deleting Streamlit before owner acceptance.
- Inventing Redraft pick metadata that the governed engine does not persist.
- Treating unavailable evidence as zero, healthy, or inferred.
