# Latest Success and Last-Known-Good Review

The receipt models the latest attempt separately from per-source success history. lifecycle.latest_attempt_receipt_id always identifies the current receipt. A successful current result sets latest_successful_receipt_id to the current receipt and leaves last_known_good_receipt_id empty.

A non-success result may reuse a prior successful receipt ID only when the same source and dataset had a prior successful row. last_known_good_receipt_id is populated only for a non-success current result that explicitly retains CURRENT_RETAINED_DATA or STALE_RETAINED_DATA. NO_USABLE_RETAINED_DATA and NOT_ENOUGH_INFORMATION do not claim a last-known-good receipt.

The lifecycle relationship is fixed to per_source_explicit_retention_only. Validation verifies closed identifiers and the service does not convert attempted refresh, retained data, or prior success into a current success claim. Refresh Recovery and Decision Trust behavior remained byte-identical to current HQ and their focused suites passed.
