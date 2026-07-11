# Append-Only Closure History Contract

## Canonical model

`METADATA_REVIEW_QUEUE.csv` is an immutable creation ledger. A future effective queue status must be computed from a new append-only closure-event ledger, proposed as `docs/hq/rookie_evidence_workspace_v1/governance/QUEUE_CLOSURE_EVENT_LEDGER.csv`. This packet does not create that ledger.

## Required event fields

Every event must contain:

1. `closure_event_id`
2. `event_type`
3. `queue_id`
4. `prior_queue_status`
5. `new_queue_status`
6. `closure_timestamp`
7. `actor_or_lane`
8. `exact_proof_artifact`
9. `proof_hash`
10. `subject_endpoint_type`
11. `subject_endpoint_id`
12. `related_endpoint_type`
13. `related_endpoint_id`
14. `authority_effect`
15. `source_use_effect`
16. `privacy_rights_result`
17. `locality_result`
18. `validation_result`
19. `commit`
20. `superseded_closure_event_id`
21. `rollback_of_event_id`
22. `record_version`

Exact endpoint fields must be populated where the category requires them. Proof hash, queue ID, effects, validation result, and commit are mandatory for a closure. Prose alone can never close a row.

## Event types

- `CLOSE_WITH_RECEIPT`: first valid closure after all category proof gates pass.
- `CORRECT_CLOSURE`: appends corrected facts and references the superseded event; it never edits the old event.
- `ROLLBACK_CLOSURE`: appends a logical reversal and references the event being rolled back.
- `REVOKE_OR_EXPIRE_PERMISSION`: records a later rights/use change without rewriting the earlier record.
- `PRIVACY_DELETION_OBLIGATION`: records a later privacy requirement and the permitted scope of removal/supersession.

## Effective-status derivation

Consumers may derive status only from the immutable creation row plus a validated chain of append-only events. An event with a missing proof hash, invalid endpoint, failed validation, broadened authority/use effect, or unresolved supersession chain is ignored and escalated. No loader may mutate the original queue row or select among conflicting events automatically.

## Corrections and rollback

Corrections are new events referencing the prior event. After canonical adoption, rollback is also a new event, followed by a superseding endpoint/link event where the registry contract requires one. Old events and proof references remain readable. Before adoption of a local lane, its unaccepted commit may be reverted; after adoption, Git history must not be used to erase the logical closure record.

## Prohibitions

Editing or deleting an old event; overwriting proof; closing without a proof hash; changing authority or use permission as a side effect; closing through prose; using path/name/semantic inference; activating deferred evidence; or storing raw/reversible restricted locators is prohibited.
