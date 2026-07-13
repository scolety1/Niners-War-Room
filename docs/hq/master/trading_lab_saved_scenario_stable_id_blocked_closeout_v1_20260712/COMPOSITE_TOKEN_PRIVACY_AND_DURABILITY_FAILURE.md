# Composite Token Privacy and Durability Failure

## Rejected identity structure

The blocked implementation persisted tokens with the representative structure:

`player:<rank>|<name>|<position>|<team>`

The pick-context variant uses the same visible identity components under a `pick_context:`
prefix. The underlying Trading Lab key generator joins these four fields:

1. final-board rank;
2. player name;
3. position;
4. NFL team.

## Durability failure

These are presentation and source facts, not stable admitted opaque identifiers. A board rerank,
trade or team correction, position-label revision, spelling/display-name change, punctuation
change, or formatting normalization can produce a different token for the same real asset. The
token therefore cannot provide durable scenario identity or dependable current-data
rehydration.

Rank-based identity and name-based identity are independently prohibited. Team, position, and
name snapshots remain prohibited even when bundled with other fields.

## Privacy and rights failure

Although the implementation described each token as opaque, its serialized value exposes the
rank, name, position, and team snapshots. Saved stores, backups, quarantine copies, and JSON
exports would repeat those prohibited display/source facts. Import accepts them again, so the
privacy and persistence allowlist fails in both directions.

No provider receipt, rights grant, authoritative service, admitted dataset, or persistence-use
approval converts these visible composites into canonical identity.

## Hashing and encoding do not cure the defect

A hash, encoding, UUID derived from, or other reversible/irreversible transformation of the same
four fields retains the same instability and lineage. It would obscure the prohibited snapshot,
not create an authoritative identifier. Such a transformation is explicitly barred from
reentry.

## Controlling result

The composite tokens must not be persisted, promoted, remapped, or treated as canonical
identity. The feature remains parked until a separately reviewed identity-authority contract
passes every reentry requirement.
