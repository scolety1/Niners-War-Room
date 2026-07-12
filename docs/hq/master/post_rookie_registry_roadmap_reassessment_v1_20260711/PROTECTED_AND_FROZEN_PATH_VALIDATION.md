# Protected and Frozen Path Validation

## Scope rule

The only allowed write prefix is:

`docs/hq/master/post_rookie_registry_roadmap_reassessment_v1_20260711/`

All files in this commit are new documentation inside that prefix. No pre-existing file is modified.

## Protected path families

The following were treated as prohibited for this lane:

- `app/` and all route/page/component behavior;
- `src/`, including services, rankings, formulas, models, draft logic, source/registry logic, and persistence;
- `tests/`;
- `config/source_registry.csv` and all source-admission/governance files;
- production data, canonical exports, local packs, and draft-day exports;
- `docs/hq/rookie_evidence_workspace_v1/` and all registry authority/queue paths;
- plugin-governance packets outside this new packet;
- all pre-existing `docs/hq/model/`, freeze, frozen, and prospective 2026 paths.

## Frozen inventory and byte check

The reproducible baseline selects every path tracked at the verified starting HQ whose name contains `frozen`, `freeze`, or `prospective_2026`, case-insensitively. Holding the starting-HQ path set fixed prevents this packet's proof filename from being mistaken for a pre-existing frozen artifact.

- Tracked file count: `120`
- Pre-staging working-tree aggregate SHA-256: `b6fa2c5c3f7d3fe800e988d7ec9a2bcb39ca7630f2f52008cdab67120bde5d7c`
- Aggregate method: sorted path, NUL, exact working-tree bytes, NUL, repeated into SHA-256
- Per-file comparison target: `git cat-file --filters HEAD:<path>`, which applies the checkout filters expected for each working-tree path
- Pre-staging byte mismatches: `0`
- Final staged pre-commit aggregate SHA-256: `b6fa2c5c3f7d3fe800e988d7ec9a2bcb39ca7630f2f52008cdab67120bde5d7c`
- Final staged pre-commit byte mismatches: `0`
- Post-commit aggregate SHA-256: `b6fa2c5c3f7d3fe800e988d7ec9a2bcb39ca7630f2f52008cdab67120bde5d7c`
- Post-commit byte mismatches: `0`

This scan covers the canonical prospective freeze packet as well as other tracked paths whose names explicitly mark them frozen/freeze/prospective.

## Registry and governance validation

- Rookie registry/queue path changes: `0`
- Source registry/admission path changes: `0`
- Plugin governance path changes outside this packet: `0`
- Formula/model/ranking implementation changes: `0`
- Live/Mock Draft implementation or state changes: `0`
- Production data/canonical export changes: `0`

## Final staged/committed scope

- Staged file count: `18`
- Staged paths outside the allowed packet: `0`
- Staged protected production paths: `0`
- `git diff --check`: PASS
- `git diff --cached --check`: PASS
- Manifest non-self hash mismatches: `0`
- Local documentation commit: PASS
- Post-commit frozen rescan: PASS
- Clean worktree after local commit: PASS
- Push: not attempted
