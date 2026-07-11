# Validation Results

## Reproduced source gates

- Scaffold validator: 118 checks, 0 issues.
- Focused tests: 38 passed.
- Governance/registry regressions: 25 passed.
- Python lint: 0 findings.
- Python compilation: 4/4 files passed.
- Controlling design/canonicalization Git-blob hashes: 33/33 passed.
- Artifact/locality/authority/schema/key/manifest/decision/locator/empty-row/relationship validations: passed.
- Absolute-path, restricted-content, off-HQ use, application-import, service-write/network scans: 0 violations.
- Source patch whitespace validation: passed.

## Merge-review gates

- Source commit parent and ancestry: pass.
- Shared canonical Git storage: pass.
- Changed paths: 48 added, 0 modified/deleted/renamed, 0 unrelated.
- Protected/frozen/ranking/formula/app/source-registry/plugin-governance changes: 0.
- Production authority true: 0/23.
- Player-value authority true: 0/23.
- Explicit source/use decisions: 0.
- Source promotion, identity resolution, evidence migration, runtime wiring: 0 each.
- Real player, alias, identity-assertion, and evidence-observation rows: 0 each.
- `git diff --check` and `git diff --cached --check`: pass before commit.

Result: `PASS_ALL_PHASE_A_PUSH_GATES`.
