# Conflict Escalation Contract

## Mandatory escalation triggers

Escalate and keep the queue row open, blocked, not-enough-information, or deferred when any of the following occurs:

- multiple explicit authorities exist for the same required relationship;
- explicit source links disagree;
- exact hashes point to different receipts or one receipt points to inconsistent hashes;
- rights, privacy, retention, or use decisions conflict;
- locality or availability classifications conflict;
- a candidate would broaden authority, source admission, retention, display, research, training, production, redistribution, or export permission;
- restricted/private evidence or a raw/reversible locator is required;
- an off-HQ artifact would need recovery, recreation, copying, or activation;
- the required canonical endpoint does not exist;
- proof depends on player identity, names, aliases, or normalized-name matching;
- a prior closure, correction, revocation, expiry, or privacy obligation conflicts with the proposed event.

## No automatic winner

No newest timestamp, preferred directory, matching filename, row count, hash frequency, public visibility, source-family default, semantic similarity, model score, or analyst preference selects a winner. Conflicting evidence is not merged, averaged, collapsed, or silently superseded.

## Escalation record

A future escalation record must contain an opaque conflict ID; affected queue IDs; candidate proof artifacts and hashes; exact endpoint IDs when available; conflict class; locality and rights classes; permission impact; actor/lane; timestamp; explicit `NO_WINNER_SELECTED`; required human/provider/governance action; and resolution event reference when one later exists. It must not copy restricted content or locators.

## Current conflict state

Five artifact subjects carry `DUPLICATE_CONFLICTING`, producing 23 queue rows. These are planning escalations. They are distinct from nine design relationship-conflict objects, zero `CONFLICTING_EXPLICIT_METADATA_LINK` queue rows, and zero rows in the explicit-link conflict output. Evidence-state conflict therefore does not become a fabricated conflicting endpoint proof.

The one protected exact-hash source candidate attached to a conflict-state artifact is excluded from the first proof-preparation batch.

## Resolution gate

Resolution requires an explicit authorized decision at the exact relationship grain, a durable proof artifact and hash, exact endpoints, recorded authority/source-use effects, rights/locality clearance, and an append-only event. Until all elements exist, closure is prohibited.
