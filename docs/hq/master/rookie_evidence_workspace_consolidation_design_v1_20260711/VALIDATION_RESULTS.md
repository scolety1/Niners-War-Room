# Validation Results

## Result

`PASS_WITH_DOCUMENTED_IDENTITY_SOURCE_AND_AUTHORITY_BLOCKERS`

The blockers are design inputs and queue candidates. They do not block the metadata-only immediate lane, but they do block player-value consolidation, source promotion, modeling, production scoring, and product integration.

| Check | Result | Evidence |
|---|---|---|
| Live-HQ verification | PASS | remote and starting branch HEAD `9368a083ae59bdb9dfc7744b90fae0c449097e1d`; no advance |
| Isolated worktree | PASS | dedicated worktree/branch; existing worktrees untouched |
| Inventory coverage | PASS | 1269 records: 1085 live, 162 local, 3 restricted locators, 19 off-HQ |
| Core rookie packet coverage | PASS | 31 packet directories, 265 files, 83 CSVs, 31,940 row occurrences inspected |
| Underlying schema review | PASS | 463 inventoried CSV schemas/row counts/hashes plus manifests/ledgers/lineage docs |
| CSV parsing | PASS | all five deliverable CSVs parsed; inventory CSV entries record parse status |
| Deliverable duplicate keys | PASS | artifact, authority, duplicate-register, and no-recreate IDs unique |
| Source duplicate discovery | PASS_WITH_FINDINGS | 20 tracked rookie CSVs contain 903 exact duplicate excess occurrences; no dedup performed |
| Internal path checks | PASS | 1,085 live files, 162 local files, 19 off-HQ Git objects, 3 restricted locators verified |
| Evidence-state consistency | PASS | allowed state enum; fail-closed canonical/blocked and identity/canonical checks |
| Cross-contract schema/enums | PASS | exact 14 evidence states, five lifecycle stages, seven orthogonal dimensions, unified queue/assertion states, normalized nine-purpose source decisions, and complete duplicate/lineage contracts |
| Identity-key review | PASS_WITH_BLOCKERS | 157/107 current chain, mixed namespaces, three no-ID current records, five missing-GSIS bridge rows, 102 missing draft IDs documented |
| Source/use consistency | PASS_WITH_BLOCKERS | no player-level production admission; narrower CFBD/use gates override broad defaults |
| Rights/privacy review | PASS_WITH_BLOCKERS | restricted/provider/private content excluded; sanitized locator policy; rights gaps documented |
| Lifecycle consistency | PASS | five stages remain separate; draft, current context, rookie, and later outcomes not flattened |
| Missingness/censoring/applicability | PASS | missing/unknown/unavailable/blocked/not-applicable distinct; 930 inapplicable threshold cases documented |
| No-recreate contradiction scan | PASS | no affirmative recreate, deletion, source promotion, UDFA inference, historical-current ADP, or execution instruction |
| Protected-path scan | PASS | zero changes outside packet |
| Frozen-artifact scan | PASS | 29 recorded files rehashed; 1 intentional absence verified; zero diffs |
| Ranking/formula/app/source-registry diff | PASS | zero changed paths |
| Plugin-governance no-change | PASS | zero changed paths; no calls or reopened research |
| `git diff --check` | PASS | executed before staging/final commit |
| `git diff --cached --check` | PASS | executed before final commit after staging |
| Manifest validation | PASS | manifest excludes its own hash; every other required file hash verified by finalizer and post-generation check |
| Clean worktree after local commit | PASS_AT_HANDOFF | required and confirmed after the final local-only commit; reported in final response |

## Inventory findings validated

- Authority families: `23`.
- Duplicate/conflict groups: `30` total; `6` exact-duplicate entries; `9` conflicting-evidence entries.
- No-recreate items: `40`.
- Duplicate-flagged inventory artifacts: `38`.
- Superseded inventory artifacts: `54`.
- Current accepted UDFA review rows remain review-only and are not verified source truth.
- No production or evidence migration occurred.

## Validation limitations

- Restricted provider files were not copied or fully reproduced in HQ; only permitted metadata/aggregate locators were validated.
- Source rights were classified from existing repository decisions; this lane did not obtain new legal permission.
- Identity blockers and evidence conflicts were documented, not resolved.
- Product behavior was intentionally not executed or modified.
