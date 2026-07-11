# Append-Only History Contract

Queue rows are immutable creation records. Claim, evidence-addition, priority-review, deferral, decision, and closure events append new history rows keyed by the queue ID and history reference. No event overwrites the original reason, status, priority basis, evidence reference, or closure requirement. Duplicate and conflict records remain separate; no loader merges or selects them.
