# Triage Contract Review

The source packet uses exactly the 12 frozen planning values:

- `POTENTIALLY_CLOSABLE_EXISTING_EXPLICIT_RECEIPT`
- `POTENTIALLY_CLOSABLE_EXISTING_EXACT_MANIFEST`
- `REQUIRES_NEW_AUTHORITY_DECISION`
- `REQUIRES_NEW_SOURCE_OR_DATASET_ENDPOINT`
- `REQUIRES_EXPLICIT_SOURCE_USE_DECISION`
- `REQUIRES_RIGHTS_OR_PRIVACY_DECISION`
- `LOCAL_ONLY_AVAILABILITY_BLOCKER`
- `RESTRICTED_LOCATOR_BLOCKER`
- `OFF_HQ_AUDIT_ONLY`
- `CONFLICTING_EVIDENCE_ESCALATION`
- `NOT_ENOUGH_INFORMATION`
- `NOT_APPLICABLE`

They are derived planning metadata only. They do not modify canonical queue status, evidence state, authority, source admission, permitted use, mapping activation, identity, or player truth. All 5,147 reconciliation rows have `canonical_row_mutation_planned=false` and `future_closure_execution_eligible=false`.

The derived primary-status reconciliation is 23 conflict, 795 local-only, 12 restricted-locator, 3 rights/privacy, 95 off-HQ, 970 new-authority, 2,166 source/dataset-endpoint, and 1,083 not-enough-information rows. The derived 1,083 does not replace the canonical `NOT_ENOUGH_INFORMATION` count of 2,700.

The classifier uses explicit queue fields and frozen precedence only. Filename, path, directory, title, proximity, semantic similarity, source-family assumptions, player or normalized names, season overlap, row counts, local cache, public accessibility, favorable content, timestamp, and model judgment are prohibited proof inputs.

Batch review reproduced 69 proof patterns and 69 batches with zero grouping issues. Rows share a group only when queue category, endpoint types, evidence class, locality, rights class, planning status, proof state, exact required proof, future permitted action, prohibited shortcuts, and closure gate are identical. Player identity, quality, draft round, fantasy relevance, ranking/formula impact, and analyst preference are not grouping inputs. Grouping reduces administrative complexity only; it does not collapse, rewrite, close, or delete canonical rows.
