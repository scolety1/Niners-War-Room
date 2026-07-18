# Last-Known-Good Contract

## Mechanical distinctions

1. Latest refresh attempt is the only valid schema/integrity-passing `latest_refresh_status.json`. Its success or failure is never replaced by backup state.
2. Latest successful refresh is historical evidence for the same canonical `source_id`/`dataset_id`. It does not prove that data is retained or current.
3. Current retained dataset requires explicit successful refresh plus existing explicit current/fresh evidence, or an explicit retained-data status already supplied by the owner.
4. Stale retained dataset requires existing explicit stale evidence. The receipt layer creates no age threshold.
5. No usable retained dataset is accepted only when explicitly recorded. In every ambiguous case the result is `NOT_ENOUGH_INFORMATION`.

## Link rule

A prior receipt ID may populate `last_known_good_receipt_id` only when the prior receipt validates under schema V1, its integrity passes, its source/dataset key exactly matches, the prior result is an explicit success, the latest result is not a success, and the latest existing metadata explicitly indicates current or stale retained data. Freshness remains separately reported from existing fields.

A valid backup is validated prior receipt evidence. It is never relabeled as the latest attempt and never establishes retained data by itself. A failed latest attempt continues to display failed even when a last-known-good link exists. Corrupt latest plus corrupt backup yields no usable receipt.

## Fail-closed examples

- Failed latest + matching prior success + explicit stale retained evidence: latest is failed, latest successful points to prior, last-known-good points to prior, retained state is stale.
- Failed latest + matching prior success + no retained evidence: latest is failed, latest successful points to prior, last-known-good is blank, retained state is not enough information.
- Failed latest + no prior: no historical or last-known-good identifier is invented.
- Missing/unsupported latest + valid backup: latest remains missing/unsupported; backup is labeled validated prior receipt only.
- Source or dataset mismatch: no link.
