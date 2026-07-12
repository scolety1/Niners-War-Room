# Trading Lab Saved Scenario Boundary

## Canonical boundary

Saved scenarios are user-authored workspace state, not canonical fantasy truth.

Allowed operations are explicit user-triggered save, load, rename, duplicate, and confirmed delete. Import/export is optional because the repository already has a bounded Development Lab JSON pattern; it may be included only after the implementation lane documents privacy, preview, confirmation, and size limits.

Allowed persisted content is limited to:

- deterministic scenario ID and schema version;
- user title and notes;
- selected asset identifiers already admitted by the Trading Lab, preserving user order;
- existing manual planner/checklist fields and user-owned states;
- creation and update timestamps;
- lifecycle metadata strictly necessary for validation, backup, quarantine, and recovery.

Forbidden persisted content includes calculated values, rankings, source-derived facts, fairness scores, recommendations, offers, plugin output, frozen comparator values, unadmitted data, inferred identities, raw provider/private receipts, or player snapshots that can silently become stale truth. Unknown identifiers remain visibly unresolved and are never remapped by name.

## Design decision required before coding

The implementation lane must first write and approve a small decision record covering:

1. storage location and environment override;
2. dedicated namespace/key;
3. schema version and supported-version policy;
4. scenario ID generation and path-safety rules;
5. authoritative player/asset identifier fields already used by Trading Lab;
6. maximum scenario count, rows, title/notes lengths, and file/import size;
7. missing, malformed, extra-key, type, and corrupt-file behavior;
8. backward compatibility and migration policy, including whether V1 supports no migration;
9. load/overwrite and delete confirmation UX;
10. export contents, privacy warning, preview, and import confirmation;
11. backup/quarantine/atomic-write lifecycle;
12. rollback by removing the dedicated storage namespace and bounded new code.

Prefer the established repository-approved local JSON lifecycle in `src/services/development_lab_state_service.py`, but use a separate Trading Lab service, schema, root, and namespace. If that pattern cannot satisfy the boundary, stop for a targeted design decision; do not invent a broad persistence framework.

No cloud synchronization, account sharing, external database, arbitrary user-selected path, plugin storage, silent autosave, or implicit overwrite is authorized.

## Corrected ready-to-paste implementation prompt

```text
# NWR MASTER CODEX REQUEST
## Trading Lab Saved Manual Scenario Workspace V1

This is one bounded implementation lane. Implement only after completing the storage decision gate below.

Do not implement Player Compare, Data Health, roster hydration, formulas, plugins, rookie-registry work, source admission, production valuation, rankings, or frozen-comparator use.

Do not add a trade calculator, fairness verdict, automated offer, recommendation, ranking adjustment, or plugin-output surface.

Commit locally only. Do not push.

---

# 1. Controlling repository state

Controlling remote branch:

`work/hq-parallel-control`

Before work:

1. Fetch all remotes.
2. Resolve the actual live remote HQ HEAD.
3. Inspect every commit after the canonical roadmap adoption.
4. Stop on conflict with Trading Lab boundaries, completed/paused work, protected systems, or frozen artifacts.
5. Create a new isolated worktree and branch from verified live HQ.
6. Do not disturb existing worktrees and never force push.

Suggested branch:

`work/trading-lab-saved-manual-scenario-workspace-v1-20260711`

Controlling roadmap packets:

`docs/hq/master/post_rookie_registry_roadmap_reassessment_v1_20260711/`

`docs/hq/master/post_rookie_registry_roadmap_canonicalization_v1_20260711/`

---

# 2. Completed work and pauses

Preserve and do not recreate:

- existing Trading Lab manual give/get selection, planner rows, notes, checklists, neutral summaries, evidence receipts, and memo/CSV exports;
- Formula Gauntlet, formula accuracy reconciliation, prospective freeze, and operational closeout;
- Decision Trust Strip;
- Refresh Recovery and Staleness UX;
- Live and Mock Draft accessibility/compact hardening;
- fantasy plugin audit/closeout;
- rookie workspace, scaffold, linkage, queue, triage, and batch 836e closeout.

Formula work remains paused pending season-complete 2026 outcomes and explicit authorization.

Plugin work remains manual-only at 0% numerical influence pending documented provider-change triggers.

Rookie queue closure remains paused under:

`ROOKIE_REGISTRY_METADATA_QUEUE_CLOSURE_PAUSED_PENDING_EXACT_CANONICAL_SOURCE_ENDPOINT_EVIDENCE`

---

# 3. Design gate before coding

Before application or service edits, write a small reviewed decision record for:

- storage location and test override;
- dedicated namespace/key;
- deterministic schema version;
- scenario ID generation and path traversal prevention;
- authoritative Trading Lab asset identifier fields;
- maximum scenarios, rows, title/notes lengths, and file/import size;
- missing/corrupt/invalid/extra-key/type handling;
- backward compatibility and migration policy;
- load/overwrite and delete confirmation;
- export privacy and import preview/confirmation;
- atomic write, prior-valid backup, quarantine, and recovery;
- rollback through removal of the new namespace and bounded code.

Prefer the established local persistence lifecycle in `src/services/development_lab_state_service.py`, with a separate Trading Lab service, schema, root, and namespace.

If no existing repository-approved pattern safely fits, stop for a targeted design decision. Do not invent a general persistence framework.

No cloud sync, account sharing, external database, arbitrary storage path, or plugin storage is allowed.

---

# 4. Required product outcome

Add a saved-scenario workspace with only explicitly user-triggered actions:

1. save current manual scenario;
2. list and load a saved scenario;
3. rename a saved scenario;
4. duplicate a saved scenario under a new deterministic ID;
5. delete a saved scenario only after positive confirmation;
6. show empty-store and no-selection states safely;
7. quarantine corrupt content and recover only from a prior validated backup;
8. optionally export/import schema-versioned JSON only if the approved design uses the existing repository pattern, previews content, warns about privacy, enforces bounds, and requires confirmation before replacement.

Do not silently autosave or overwrite. Loading/importing over non-empty session state requires preview and positive confirmation.

---

# 5. Persisted allowlist

Persist only:

- deterministic scenario ID;
- deterministic schema version;
- user-entered title and notes;
- selected asset identifiers already admitted by the existing Trading Lab, preserving user order;
- existing user-authored planner/checklist fields and states;
- creation and update timestamps;
- minimal lifecycle metadata for validation, backup, quarantine, and recovery.

Persist stable admitted keys, not names or computed display facts. Unknown/stale identifiers remain visible as unresolved / Not enough information and are never remapped by player name.

---

# 6. Forbidden persisted fields and effects

Do not save, copy, generate, or make authoritative:

- calculated trade values, package totals, formulas, projections, scores, fairness labels, winners, recommendations, or offers;
- rankings or ranking adjustments;
- external plugin output or provider calls;
- hidden NWR recommendations;
- frozen PYF, GAUNTLET_081, current-board, or other prospective comparator values;
- unadmitted source data;
- player snapshots or source-derived facts that can silently become stale truth;
- inferred identities or name-fallback mappings;
- raw private/provider receipts;
- rookie registry/queue data;
- Live Draft or Mock Draft picks, events, namespaces, or state.

Any need for a forbidden field or system is a stop condition.

---

# 7. Interaction and accessibility

- Give save, load, rename, duplicate, delete, import, export, overwrite, quarantine, and recovery controls explicit accessible names.
- Keep controls keyboard-operable and legible at compact widths.
- Convey success, error, unresolved key, quarantine, recovery, and confirmation state in text, not color alone.
- Use neutral human-in-the-loop copy; never imply that NWR judged the trade.

---

# 8. Required tests

At minimum test:

1. empty store and first save;
2. allowlisted round trip preserving order, notes, planners, and checklists;
3. explicit rename, duplicate with new ID, and delete confirm/cancel;
4. scenario-count and field/file-size bounds;
5. unknown/extra fields and invalid types rejected before session mutation;
6. unsupported schema with no session mutation;
7. stale/unknown asset identifiers remain unresolved with no name fallback;
8. load/import preview and positive overwrite confirmation;
9. atomic replacement and prior-valid backup;
10. corrupt latest quarantine and validated-backup recovery;
11. dedicated temporary test root and path traversal rejection;
12. creation/update timestamp behavior;
13. Live and Mock Draft state snapshots unchanged after every operation;
14. existing Trading Lab memo/CSV exports unchanged;
15. no ranking, formula, source registry, plugin, rookie registry, data pack, production, or frozen-artifact diff;
16. neutral guardrail copy with no value/score/winner/fairness/recommendation/offer claim;
17. focused keyboard, status-message, and compact-width checks.

Reproduce the clean-HQ/source/final differential for `tests/test_trust_banner_ui.py`. Its known baseline is `2 failed, 3 passed`; do not weaken or rewrite those unrelated tests.

---

# 9. Expected scope

Expected implementation files are limited to:

- `app/pages/23_trading_lab_v1.py`;
- one narrowly named Trading Lab scenario-state service under `src/services/`;
- focused tests under `tests/`;
- one new lane packet under `docs/hq/master/`.

Do not modify navigation, Player Compare, Data Health, roster tools, rankings, formulas, source registry/admission, plugins, rookie registry/queue, draft services/pages, production data, or frozen artifacts.

---

# 10. Validation and delivery

Validate live-HQ ancestry, the approved storage decision, focused lifecycle tests, existing Trading Lab tests, Live/Mock isolation, route smoke, existing memo/CSV downloads, untracked storage root, protected paths, frozen bytes, `git diff --check`, `git diff --cached --check`, and a clean worktree after one local commit.

Use a separate independent merge-review lane. Do not push the implementation lane.

The lane passes only if users can deliberately resume their own manual work while every protected decision/governance system remains unchanged.
```
