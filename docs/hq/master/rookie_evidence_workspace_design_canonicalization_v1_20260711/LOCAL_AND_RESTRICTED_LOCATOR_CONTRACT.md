# Local and Restricted Locator Contract

## Inventory baseline

The unchanged source inventory contains exactly:

- `1,085` `LIVE_HQ` locators;
- `162` `LOCAL_ONLY` locators;
- `3` `LOCAL_ONLY_RESTRICTED` sanitized locators;
- `19` `OFF_HQ_BRANCH_ONLY` Git-object locators.

Every record already has an opaque `artifact_id`. The future scaffold must retain that ID and create a separate sanitized locator record. A path string is never an artifact ID.

## Live-HQ paths

A `LIVE_HQ` path may be registered as a repository-relative artifact location. It is not a player identity, player key, source authority, use decision, proof of truth, or proof that its contents are admitted for any purpose.

## Local-only paths

Absolute paths such as `C:/NWR_REVIEW/...` and `C:/NWR_SHARED_DATA/...` are discovery and audit locators only. They must never become:

- primary or foreign keys;
- canonical artifact IDs;
- runtime dependencies;
- application data paths;
- user-facing links;
- evidence authority;
- source-admission evidence;
- proof of persistent availability.

The scaffold may store the existing opaque `artifact_id`, `locality_class=LOCAL_ONLY`, a non-reversible sanitized locator ID, permitted integrity metadata, and an availability state. It must not require the absolute path at runtime. Missing local content remains missing or unavailable; it is not recreated.

## Restricted locators

For `LOCAL_ONLY_RESTRICTED`, only these may enter HQ:

- opaque `artifact_id`;
- non-reversible `restricted_locator_id` or existing sanitized scheme identifier;
- locality, lifecycle, evidence-state, rights-state, privacy-class, and review-status metadata;
- permitted aggregate counts;
- permitted integrity metadata when it does not reveal or enable reconstruction of a private/provider locator;
- governing decision and no-recreate links.

Raw content, raw receipts, private identifiers, credentials, provider prose, substantial provider output, exact private paths, and reversible private/provider locator material are prohibited. A restricted locator must pass an allowlist check and a reversibility review before registration.

## Off-HQ Git-object locators

An `OFF_HQ_BRANCH_ONLY` locator may retain the immutable commit plus repository-relative object path for no-recreate and audit discovery only. It must carry `LOCAL_ONLY_RESTRICTED`, `SOURCE_UNADMITTED`, and `USE_BLOCKED` semantics for active downstream use.

It may not become active evidence, a source fact, a migration source, a player-value observation, a formula or ranking input, a canonical ranking, training data, production data, or application data. Existence of a Git object does not authorize cherry-picking or copying it.

## Non-key and sanitization validation

The scaffold validator must reject:

- any primary or foreign key whose value matches an absolute path, `LOCAL_ONLY_RESTRICTED://`, or `git:<commit>:` locator pattern;
- a local or restricted locator used as `artifact_id`;
- a runtime or user-facing field containing a local or off-HQ locator;
- a restricted record containing a raw path or reversible private/provider locator;
- an off-HQ record with an allowed source/use/ranking/formula/production state;
- silent recreation when a local or off-HQ locator cannot be resolved.

No locator class implies authority, availability, identity, permission, or truth.
