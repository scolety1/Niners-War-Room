# Authority Field Normalization Contract

## Controlling rule

`AUTHORITY_CANONICALITY_NORMALIZED.csv` is the controlling machine-readable authority interpretation for `Rookie Evidence Registry Read-Only Scaffold V1`.

The source column `EVIDENCE_AUTHORITY_CLASSIFICATION.csv.canonical_now` is preserved unchanged as historical design evidence and is classified, for every row, as:

`NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD`

It must never be parsed as Boolean, truthiness, generic canonicality, admission, authority, permission, precedence, or promotion. Values such as `true`, `scope_limited`, `decision_receipt_only`, `true_for_policy`, `false_local_review`, and `false_consumer` are opaque legacy strings only.

## Required columns

- `authority_id`: exact source authority ID; unique and non-null.
- `evidence_family`: copied label for reviewability; not a key.
- `metadata_registration_status`: the only metadata registration action permitted by this row.
- `authority_scope_class`: closed interpretation of what the row can govern.
- `player_value_authority`: strict lowercase Boolean; must be `false` for this version.
- `production_authority`: strict lowercase Boolean; must be `false` for this version.
- `source_admission_effect`: current effect on source admission; none of its values grants admission.
- `locality_class`: locality of the controlling artifact locator in the source authority row, not proof that referenced evidence is available.
- `permitted_use_class`: maximum metadata-only use permitted to the scaffold.
- `controlling_caveat`: mandatory fail-closed qualification.
- `legacy_canonical_now_value`: exact historical string from the source row.
- `legacy_field_interpretation`: exact constant `NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD`.
- `source_authority_row`: immutable row locator in the source packet.

## Closed values

### `metadata_registration_status`

- `REGISTER_AUTHORITY_METADATA`
- `REGISTER_LOCATOR_METADATA_ONLY`
- `REGISTER_NO_RECREATE_METADATA_ONLY`
- `REGISTER_DEPENDENCY_METADATA_ONLY`

### `authority_scope_class`

- `GOVERNANCE_POLICY_ONLY`
- `PROTECTED_EVALUATION_POLICY_ONLY`
- `SOURCE_FAMILY_ROUTING_CEILING_ONLY`
- `RECEIPT_STANDARD_ONLY`
- `EVIDENCE_REVIEW_ONLY`
- `DECISION_RECEIPT_ONLY`
- `BLOCK_POLICY_ONLY`
- `LOCAL_REVIEW_LOCATOR_ONLY`
- `OFF_HQ_AUDIT_LOCATOR_ONLY`
- `NO_RECREATE_REFERENCE_ONLY`
- `PRODUCT_DEPENDENCY_REFERENCE_ONLY`

### Boolean fields

Only exact lowercase `true` and `false` are syntactically valid. For V1, both `player_value_authority` and `production_authority` are fixed to `false` for all 23 rows. No other field may be coerced to Boolean.

### `source_admission_effect`

- `NO_SOURCE_ADMISSION`
- `ROUTING_CEILING_ONLY`
- `SEPARATE_EXPLICIT_DECISION_REQUIRED`
- `BLOCKS_ADMISSION`

All four values are non-admitting. `ROUTING_CEILING_ONLY` can only route a candidate toward a narrower gate. `SEPARATE_EXPLICIT_DECISION_REQUIRED` denies admission until an explicit dataset, field-family, purpose, and receipt decision exists. `BLOCKS_ADMISSION` is an affirmative current block. There is no admitting value in this contract.

### `locality_class`

- `LIVE_HQ`
- `LOCAL_ONLY`
- `OFF_HQ_BRANCH_ONLY`

Locality describes a locator class only. It is not identity, authority, availability proof, persistence proof, or permission.

### `permitted_use_class`

- `GOVERNANCE_METADATA_ONLY`
- `PROTECTED_EVALUATION_POLICY_METADATA_ONLY`
- `RECEIPT_STANDARD_METADATA_ONLY`
- `REVIEW_METADATA_ONLY`
- `DECISION_RECEIPT_METADATA_ONLY`
- `BLOCKER_METADATA_ONLY`
- `LOCAL_LOCATOR_METADATA_ONLY`
- `OFF_HQ_AUDIT_METADATA_ONLY`
- `NO_RECREATE_METADATA_ONLY`
- `DEPENDENCY_METADATA_ONLY`

These classes authorize metadata registration only. They do not authorize use of the underlying evidence.

## Non-implication rules

- Governance canonicality does not imply evidence canonicality.
- Review canonicality does not imply player-value truth.
- A decision receipt does not imply source truth or identity truth.
- A live-HQ locator does not imply player-value, formula, ranking, training, or production authority.
- Local-only and off-HQ evidence remains locator/reference metadata only.
- Conflicting evidence cannot be selected, merged, preferred, or reconciled automatically.
- Source-family defaults cannot override narrower dataset, field, purpose, identity, receipt, rights, privacy, or use blockers.
- No authority row grants automatic source promotion.
- No authority row grants formula, ranking, model-training, production-scoring, application, or product-facing use.

## Fail-closed parsing

Reject the normalized file if the row count is not exactly 23; an authority ID is missing or duplicated; a closed value is unknown; either Boolean is not exactly `false`; the legacy interpretation constant differs; a source-row locator is missing; or any source-admission effect is treated as an admission. Do not fall back to the legacy field or prose.
