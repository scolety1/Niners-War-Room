# Scaffold Entry and Population Lock

## Immediate lane

The immediate lane remains exactly:

`Rookie Evidence Registry Read-Only Scaffold V1`

This canonicalization packet does not execute that lane.

## Permitted population

The future scaffold may populate only:

- artifact, source, dataset, receipt, and authority metadata;
- explicit field, dataset, and use decisions with supporting receipts;
- lifecycle and state dictionaries;
- duplicate and conflict relationships;
- no-recreate relationships;
- sanitized locator metadata;
- implementation and validation status.

## Prohibited population

It must not populate:

- player-value observations or source facts;
- canonical player records, aliases, or identity resolutions;
- identity assertions based on real evidence;
- inferred UDFA values or confirmed-UDFA claims derived from absence or review status;
- rookie rankings, formula inputs, model/training rows, production-scoring rows, recommendations, or product-facing data;
- raw local, restricted, provider, private, or off-HQ evidence.

Player, alias, identity-assertion, and evidence-observation schemas must remain empty except for clearly labeled, non-real, non-player synthetic validation fixtures. Synthetic fixtures must use impossible fixture IDs, carry `SYNTHETIC_VALIDATION_FIXTURE`, and be excluded from every export and count of real evidence.

## Required controls

- Consume `AUTHORITY_CANONICALITY_NORMALIZED.csv`; never parse `canonical_now`.
- Enforce exactly 23 unique authority rows and all normalized Boolean and enum checks.
- Separate opaque artifact IDs from sanitized locator records.
- Enforce one explicit decision per dataset, field family, purpose, and version.
- Reject admission derived from family defaults, accessibility, prose, review history, identity approval, recency, or favorable values.
- Preserve existing evidence in place and preserve all duplicate/conflict and no-recreate relationships.
- Remain read-only and non-destructive.

## Corrected ready-to-paste scaffold prompt

```text
# NWR MASTER CODEX REQUEST
## Rookie Evidence Registry Read-Only Scaffold V1

Build only the metadata-first, read-only Rookie Evidence Registry scaffold authorized by canonical HQ.

Controlling remote branch: work/hq-parallel-control
Resolve and verify the live remote HEAD before work. Fetch all remotes, inspect any advance, stop on an incompatible governance/protected/frozen change, create an isolated worktree, and never force push.

Controlling design packets:
- docs/hq/master/rookie_evidence_workspace_consolidation_design_v1_20260711/
- docs/hq/master/rookie_evidence_workspace_design_canonicalization_v1_20260711/

The canonicalization packet controls machine interpretation. Consume AUTHORITY_CANONICALITY_NORMALIZED.csv. Never parse EVIDENCE_AUTHORITY_CLASSIFICATION.csv.canonical_now; it is NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD.

Implement only empty/read-only registry structure, closed dictionaries, validators, and permitted metadata population for:
- artifact metadata;
- source metadata;
- dataset metadata;
- receipt metadata;
- explicit field/dataset/use decisions;
- authority metadata;
- lifecycle and state dictionaries;
- duplicate/conflict relationships;
- no-recreate relationships;
- sanitized locator metadata;
- implementation and validation status.

Do not populate real player rows, player values, canonical players, aliases, identity assertions, evidence observations, source facts, inferred or confirmed UDFA values, rankings, formula inputs, model/training data, production-scoring data, recommendations, app data, or product-facing data. Player, alias, identity-assertion, and evidence-observation schemas must remain empty except for unmistakably synthetic validation fixtures that cannot enter exports or real counts.

Use the existing opaque artifact_id plus a separate sanitized locator record. Repository-relative LIVE_HQ paths are locations only. Absolute LOCAL_ONLY paths are discovery/audit locators only and may not be keys, runtime dependencies, app paths, user-facing links, authority, or availability proof. LOCAL_ONLY_RESTRICTED records may contain only non-reversible sanitized locator IDs, permitted aggregates/integrity metadata, and governance metadata. OFF_HQ_BRANCH_ONLY Git locators are no-recreate/audit-discovery metadata only; they remain source-unadmitted and use-blocked. Never silently recreate a missing artifact.

Create one versioned source/use decision for each dataset_id × field_family × purpose only when an existing explicit decision or receipt supports that exact grain. Purposes are exactly LOCAL_RETENTION, CANONICAL_HQ_SUMMARY, RAW_RECEIPT_STORAGE, DISPLAY, RESEARCH, MODEL_TRAINING, PRODUCTION_SCORING, REDISTRIBUTION, and EXPORT. Decision values are exactly ALLOWED, ALLOWED_WITH_CAVEATS, REVIEW_ONLY, BLOCKED, NOT_ENOUGH_INFORMATION, and NOT_APPLICABLE. Do not infer permission from family defaults, access, local caches, public visibility, prior review use, human identity approval, newer artifacts, favorable values, hashes, or prose. Missing decisions fail closed with NOT_ENOUGH_INFORMATION plus SOURCE_UNADMITTED, USE_BLOCKED, or LOCAL_ONLY_RESTRICTED in the appropriate separate state dimensions.

Enforce: production_authority=false and player_value_authority=false for all 23 normalized authority rows; no automatic source promotion; no formula/ranking/training/production grant; governance canonicality does not imply evidence canonicality; review canonicality does not imply player truth; decision receipts do not imply source truth; conflicting evidence cannot be selected automatically; narrower blockers override source-family defaults.

Preserve all existing evidence in place. Do not migrate, copy, consolidate, deduplicate, rewrite, resolve identities, promote sources, change rankings/formulas/app behavior/production data/draft behavior/recommendations/plugin governance, or modify frozen 2026 artifacts.

Validate exact row/enums/keys, zero real player/evidence rows, no raw or reversible restricted locators, no local paths in keys/runtime/user-facing fields, no off-HQ active use, no source promotion, no identity resolution, no evidence migration, privacy/rights, protected/frozen paths, ranking/formula/app/source-registry/plugin-governance diffs, git diff --check, staged diff check, and clean state after normal non-force push.

Return to Master HQ if any permission or mapping would require guessing.
```
