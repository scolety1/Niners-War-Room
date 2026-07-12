# Next Lane Ready-to-Paste Prompt

```text
# NWR MASTER CHATGPT WORK REQUEST
## Trading Lab Saved Manual Scenario Workspace V1

This is one bounded Niners War Room implementation lane.

Implement the ability to explicitly save, resume, back up, import, and safely recover human-entered Trading Lab scenarios.

Do not add a trade calculator, value, score, package total, fairness verdict, winner, recommendation, or automated offer.

Do not change rankings, formulas, projections, sources, source admission, draft logic, production data, rookie registry systems, plugin governance, or frozen 2026 artifacts.

Do not call or integrate Flaim or FantasyBot. External numerical influence remains 0%.

Commit locally only. Do not push.

---

## 1. Controlling repository state

Controlling remote branch:

`work/hq-parallel-control`

Before work:

1. Fetch all remotes.
2. Resolve the actual live HEAD of `work/hq-parallel-control`.
3. Inspect every intervening commit from the roadmap-reassessment base if HQ has advanced.
4. Stop if an advance conflicts with protected systems, frozen artifacts, source/plugin/registry governance, or this lane.
5. Create a new isolated worktree and branch from verified live HQ.
6. Do not disturb existing worktrees.

Suggested branch:

`work/trading-lab-saved-manual-scenario-workspace-v1-20260711`

All production edits must remain within the explicitly approved Trading Lab page, one narrowly named scenario-state service, focused tests, and a new lane documentation packet.

---

## 2. Controlling completed work and pauses

Treat these as complete and do not recreate them:

- Trading Lab manual give/get rows, neutral summary, roster context, notes, checklists, evidence receipts, and CSV/memo exports;
- Decision Trust Strip and Evidence Consistency V1;
- Refresh Partial-Failure Recovery and Staleness UX V1;
- Live and Mock Draft Accessibility / Compact-Width Hardening V1;
- all formula and prospective freeze work;
- plugin capability audits and closeout;
- rookie evidence workspace, registry scaffold, linkage, queue, triage, and batch 836e closeout.

Controlling pauses:

`PROSPECTIVE_2026_FREEZE_OPERATIONALLY_CLOSED_PENDING_FUTURE_OUTCOMES`

`ROOKIE_REGISTRY_METADATA_QUEUE_CLOSURE_PAUSED_PENDING_EXACT_CANONICAL_SOURCE_ENDPOINT_EVIDENCE`

Flaim: `USEFUL_MANUALLY_NOT_READY_FOR_ADAPTER`

FantasyBot: `MANUAL_EXTERNAL_SECOND_OPINION_ONLY`

---

## 3. Required product outcome

Using the existing manual Trading Lab fields, add an explicit local workspace that lets a user:

1. save the current manual scenario;
2. list and load saved scenarios;
3. preview JSON import before it changes the current session;
4. explicitly confirm replacement of a non-empty current scenario;
5. export/import a schema-versioned JSON backup;
6. recover from a prior valid backup when the latest local file is corrupt;
7. quarantine corrupt content without deleting it;
8. reset a saved scenario only after confirmation.

Preserve the existing CSV and memo downloads unchanged.

---

## 4. Data and persistence contract

Define and test an explicit allowlist of existing human-editable fields only:

- scenario identifier, user title, and user notes;
- selected trade-away and trade-for stable asset keys in user-selected order;
- manual grouping or row order already represented by the page;
- user-owned checklist states;
- schema version and local lifecycle timestamps.

Persist stable keys, not computed display facts. Unknown or stale keys must remain visible as unresolved/not enough information. Never remap by player name.

Use a dedicated application-local untracked storage root with an environment override for tests. Sanitize identifiers. Never construct paths from unchecked titles. Bound file size, title, notes, and row counts. Reject unexpected keys and types before session mutation.

Use same-directory temporary writes, flush, atomic replace, prior-valid backup, schema validation, and corrupt-file quarantine. Missing storage is an empty workspace, not an application error.

Do not silently autosave or overwrite. Load/import over non-empty state requires preview and positive confirmation.

---

## 5. Forbidden fields and effects

Do not persist or create:

- rankings, source-derived facts, projections, formulas, values, scores, package totals, fairness labels, winners, recommendations, or offers;
- Flaim/FantasyBot data, calls, adapters, or fields;
- rookie registry data, mappings, identities, locators, endpoints, authority, or queue state;
- Live Draft or Mock Draft picks, events, namespaces, or state;
- frozen prospective comparator content;
- arbitrary filesystem paths.

Any need for these is a stop condition.

---

## 6. Accessibility and interaction

- Give every save/load/import/overwrite/reset/recovery control an explicit accessible name.
- Keep all controls keyboard-operable at compact widths.
- Convey success, error, quarantine, recovery, and unresolved-key states in text, not color alone.
- Keep copy neutral and human-in-the-loop; do not imply the application judged the trade.

---

## 7. Required tests

At minimum test:

1. empty store and first save;
2. allowlisted round trip with order, notes, and checklists;
3. unknown/extra fields and type rejection;
4. schema mismatch with no session mutation;
5. stale/unknown asset keys and no name fallback;
6. import preview and explicit overwrite confirmation;
7. atomic replacement and backup creation;
8. corrupt latest quarantine and prior-valid-backup recovery;
9. reset confirm/cancel;
10. dedicated test root and path traversal rejection;
11. Live and Mock Draft state snapshots unchanged after every operation;
12. no ranking, formula, source registry, plugin, rookie registry, data-pack, or frozen-artifact diff;
13. neutral guardrail copy with no score/winner/fairness/recommendation claim;
14. focused keyboard/accessibility and compact-width behavior for new controls.

Run the existing focused Trading Lab and Live/Mock isolation suites as regression checks.

---

## 8. Expected implementation scope

Expected code/test files:

- `app/pages/23_trading_lab_v1.py`;
- one narrowly named Trading Lab scenario-state service under `src/services/`;
- focused tests under `tests/`;
- a new documentation packet under `docs/hq/master/`.

Any need to modify navigation, rankings, formulas, source registry, plugins, rookie registry, draft services/pages, production data, or frozen artifacts is a stop condition.

---

## 9. Validation and delivery

Validate:

- verified live HQ and intervening commits;
- focused persistence lifecycle tests;
- existing Trading Lab tests;
- Live/Mock state isolation;
- Trading Lab route smoke and existing CSV/memo downloads;
- storage root remains untracked;
- protected-path and frozen-byte scans;
- `git diff --check`;
- `git diff --cached --check`;
- clean worktree after a local commit.

Use one implementation worktree and a separate independent merge-review lane. Commit locally only. Do not push.

The lane passes only if a user can deliberately resume manual work and every protected decision/governance system remains unchanged.
```
