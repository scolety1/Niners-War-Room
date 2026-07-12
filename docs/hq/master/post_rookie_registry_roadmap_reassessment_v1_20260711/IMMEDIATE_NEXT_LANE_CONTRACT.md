# Immediate Next Lane Contract

## Lane

**Trading Lab Saved Manual Scenario Workspace V1**

Classification: `READY_NOW_MODERATE_RISK`

This contract authorizes one bounded implementation lane and one independent merge-review lane. It does not authorize implementation in this reassessment.

## Problem

Trading Lab already supports manual asset rows, neutral summaries, roster context, notes, checklists, evidence receipts, and CSV/memo downloads. Its working scenario is stored in Streamlit session state. A browser refresh, process restart, or session loss can therefore discard a user's unfinished manual analysis.

## Required outcome

Add an explicit, local, reversible workspace that lets a user:

1. save the current manual scenario;
2. list and load saved scenarios;
3. preview an import before it changes the current session;
4. explicitly confirm replacement of a non-empty current scenario;
5. export/import a schema-versioned JSON backup;
6. recover from a prior valid backup when the latest local file is corrupt;
7. quarantine corrupt content without deleting it;
8. reset a saved scenario only after confirmation.

## Allowed persisted fields

The implementation must define and test an explicit allowlist derived from existing human-editable Trading Lab controls, such as:

- scenario identifier, user-entered title, and user-entered notes;
- trade-away and trade-for asset keys in user-selected order;
- manual asset grouping or row order already represented by the page;
- user-owned checklist states;
- schema version and local timestamps needed for lifecycle handling.

Persist stable keys rather than computed display facts. A stale or unknown key must load as unresolved/not enough information and remain visible for manual correction. It must never be remapped by player name.

## Forbidden persisted fields and effects

Do not persist or create:

- ranking values, source-derived facts, projections, formulas, values, scores, package totals, fairness labels, winners, recommendations, or automated offers;
- Flaim or FantasyBot content, calls, adapters, fields, or numerical influence;
- rookie registry rows, mappings, endpoints, identities, locators, authority, or queue state;
- Live Draft or Mock Draft picks, events, session namespaces, or persisted state;
- frozen PYF, GAUNTLET_081, current-board, or other prospective comparator content;
- arbitrary filesystem paths or user-selected write locations;
- autosave that silently overwrites a current or saved scenario.

## Storage contract

- Use a dedicated application-local, untracked storage root with an environment override for tests.
- Use deterministic, sanitized scenario identifiers; never construct a path from an unchecked title.
- Write a temporary file in the same directory, flush it, and atomically replace the target.
- Retain a prior valid backup before replacement.
- Validate schema and types before any session-state mutation.
- Quarantine invalid/corrupt files with an auditable reason; do not delete them automatically.
- Bound title, notes, row count, and file size; reject unexpected keys.
- Treat missing storage as an empty workspace, not an application failure.
- Preserve current manual exports; JSON backup is additive and must not change existing CSV/memo semantics.

## Interaction and accessibility contract

- Save, load, import, overwrite, reset, and recovery actions must be explicit and separately labeled.
- Loading or importing over a non-empty session requires a preview and positive confirmation.
- Status, error, quarantine, and recovery results must be conveyed in text, not color alone.
- All controls require accessible names and keyboard operation at compact widths.
- Copy must remain neutral and human-in-the-loop; it may not imply that the application evaluated trade fairness.

## Required tests

At minimum:

1. empty-store and first-save behavior;
2. allowlisted round trip preserving order and manual checklist/notes;
3. unknown and extra field rejection;
4. schema-version mismatch with no session mutation;
5. stale/unknown asset key remains unresolved with no name fallback;
6. import preview and explicit overwrite confirmation;
7. atomic replacement and backup creation;
8. corrupt latest-file quarantine and prior-valid-backup recovery;
9. confirmed reset and cancel behavior;
10. dedicated test storage root and path traversal rejection;
11. Live Draft and Mock Draft state snapshots unchanged across save/load/import/reset;
12. no ranking, formula, source registry, plugin, rookie registry, data pack, or frozen-artifact diff;
13. guardrail copy contains no score, winner, fairness, or recommendation claim;
14. focused keyboard/accessibility and compact-width checks for new controls.

## Implementation scope

Expected files are limited to:

- `app/pages/23_trading_lab_v1.py`;
- one narrowly named Trading Lab scenario-state service under `src/services/`;
- focused tests under `tests/`;
- lane documentation under a new `docs/hq/master/` packet.

Any need to modify navigation, rankings, formulas, source registry, plugins, rookie registry, draft services/pages, production data, or frozen artifacts is a stop condition and requires a new contract.

## Validation and rollback

- Run focused scenario-state and Trading Lab tests plus existing Live/Mock state-isolation tests.
- Run route smoke for Trading Lab and verify current CSV/memo downloads still work.
- Run protected-path and frozen-byte scans.
- Verify the storage root is untracked and test roots are temporary.
- Rollback is removal of the new service/UI controls/tests and deletion of the local untracked scenario store; existing Trading Lab manual behavior must remain intact.

## Acceptance gate

The lane passes only if users can intentionally resume manual work while the application remains neutral and every protected system is unchanged. A working persistence feature with any automated evaluation, hidden derived data, implicit overwrite, or cross-surface state mutation fails the lane.
