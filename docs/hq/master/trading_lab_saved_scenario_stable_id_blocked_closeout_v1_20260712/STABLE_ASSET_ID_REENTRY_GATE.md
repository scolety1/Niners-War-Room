# Stable Asset ID Reentry Gate

Controlling status:
`TRADING_LAB_SAVED_SCENARIO_WORKSPACE_PAUSED_PENDING_STABLE_ADMITTED_ASSET_IDENTIFIERS`

Saved-scenario persistence may not reenter implementation until Master HQ separately reviews and
approves an identity-authority contract. The contract must cover every persisted asset type in
the proposed scope.

## Mandatory proof for each supported asset type

1. Exact stable opaque asset ID.
2. Explicit identifier namespace.
3. Authoritative originating service or admitted dataset.
4. Uniqueness proof.
5. Availability for every selectable asset in the proposed saved-scenario scope.
6. Stability across rank changes.
7. Stability across NFL-team changes.
8. Stability across position-label changes.
9. Stability across name/display changes.
10. No construction from presentation fields.
11. No name fallback.
12. Explicit persistence-use approval.
13. Current-data rehydration contract.
14. Unresolved-ID behavior.
15. Import/export privacy contract.

The proof is conjunctive: missing or partial evidence for any item keeps that asset type blocked.
Indirect/composite match counts do not satisfy availability, uniqueness, authority, or
persistence-use approval.

## Asset-type boundaries

Rookie players and dropped veterans require an admitted player-identity contract covering every
selectable row in scope. Draft-pick and pick-context assets require their own stable admitted
namespace and authority. A player ID cannot substitute for a pick or pick-context ID.

No agent may create a new identity namespace merely to unblock persistence. A future lane may
narrow product scope only after explicit HQ approval and before implementation; it may not
silently omit unsupported asset types.

## Reentry trigger and sequence

A new identity-authority trigger must be concrete: an admitted service/dataset and reviewed
contract supplying the proofs above. Repeating the same stable-ID search without that trigger is
prohibited.

After the authority contract passes, a separate implementation lane must still obtain explicit
schema, migration/non-migration, unresolved-ID, privacy, import/export, storage, and behavior
approval. This packet grants none of those approvals.

The future design candidate is `Trading Lab Stable Asset Identity Authority Design and Readiness
V1`. It remains parked until Master HQ explicitly prioritizes identity infrastructure over the
current roadmap.
