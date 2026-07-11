# Archive and Retention Policy

## Archive means logical retirement

No evidence is deleted, moved, or rewritten merely because it is old, duplicated, superseded, conflicting, local-only, blocked, or incomplete. Archive is a manifest state and optional read-only view, not a destructive filesystem operation.

## Retention classes

| Class | Examples | Minimum treatment |
|---|---|---|
| `IMMUTABLE_PROTECTED` | prospective 2026 freeze, human decision receipts, source receipts | retain bytes, hashes, commit, policy; never edit in place |
| `CANONICAL_POLICY` | roadmap, no-recreate, receipt and state contracts | retain every version and supersession chain |
| `CANONICAL_REVIEW_ONLY` | positive draft admission, scoped gate decisions, compact label review source | retain bytes and purpose limits; never promote by archive action |
| `SUPPORTING_EVIDENCE` | audits, coverage matrices, independent systems | retain until explicit retention decision; preserve relationships |
| `SUPERSEDED_RETAIN` | Gate F V1-V4, early blockers, stale predecessors | exclude from default current view only after parity; retain for rollback |
| `DUPLICATE_EQUIVALENT_RETAIN` | exact tracked/local copies, repeated assertion rows | retain all source assertions; store equivalence proof |
| `DUPLICATE_CONFLICTING_RETAIN` | competing scoring/target/draft values | retain all; conflict remains visible until closure receipt |
| `LOCAL_ONLY_RESTRICTED` | provider exports, recovered matrices, raw/private receipts | retain according to rights/privacy; canonical HQ stores sanitized locator only |
| `UNAVAILABLE_OR_MISSING_RECORD` | coverage/unavailability events | retain expectation and state history, not a fabricated value |

## Archive eligibility

An artifact may be marked logically archived only after:

- a successor or current view is explicitly named;
- all bytes/hashes, schemas, row counts, and source receipts are recorded where permitted;
- field/population/authority parity passes;
- duplicate and conflict relationships are preserved;
- no-recreate and rollback references exist;
- source rights permit the planned retained form;
- human approval signs the archive decision.

Archive eligibility never authorizes deletion.

## Restricted data

- Do not copy restricted raw/provider/private content into HQ for convenience.
- Store a sanitized `restricted_locator_id`, classification, source family, aggregate counts, permitted hash status, retention owner, and access decision.
- Do not store credentials, private identifiers, substantial provider content, or reversible private keys.
- Rights-expiration or deletion obligations override ordinary retention and require a separate legal/privacy closure receipt; the canonical registry retains only the minimum allowed audit record.

## Hash and manifest retention

- SHA-256 is the default integrity hash.
- Preserve source hash, normalized hash, schema fingerprint, byte count, row count, column count, and Git object/commit when permitted.
- A hash proves bytes, not authority or rights.
- Restricted hashes may be withheld if the digest/path itself is not permitted; record the withholding decision.
- Manifests are deterministically ordered, versioned, and append-only.

## Superseded versions

V1-V4 display artifacts, early Gate C packets, current draft-capital V1, older Outcome sources, legacy fixtures, and stale policies stay accessible. Default views may point to a later version only with a scoped supersession decision. Corrections use new versioned artifacts and never overwrite a prior version.

## Duplicate retention

Exact duplicates remain because location, commit, receipt, rights, and authority may differ even when bytes match. Schema-equivalent or row-equivalent derivatives remain because transformations and scopes differ. A future storage optimization may use content-addressed backing only after legal, rollback, and source-location requirements are proven; logical records for every original copy remain.

## Conflict retention

Competing values are retained indefinitely unless an approved correction establishes one source as erroneous for a specific scope. Even then, the incorrect assertion remains with `evidence_state=SUPERSEDED` or the separately governed `assertion_status=REJECTED` and its closure receipt. `REJECTED` is not an evidence state.

## Rollback

Every archive/supersession decision records the predecessor path/locator, hash, successor, effective date, validation, and restore procedure. If an original cannot be restored or accessed under its permitted retention boundary, archive is blocked.

## Prohibited archive actions in this lane

- moving files into an archive directory;
- deleting duplicate rows or files;
- renaming old packets;
- rewriting manifests or evidence;
- copying local-only raw data into HQ;
- treating an archive label as a source/use promotion;
- changing the frozen 2026 packet.
