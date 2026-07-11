# Rights, Privacy, and Locator Boundary

Locator presence never authorizes active use. The exact canonical boundary is:

| Locality | Artifacts | Queue rows | Availability | Rights | Privacy | Active use |
|---|---:|---:|---|---|---|---|
| `LIVE_HQ` | 1,085 | 4,227 | `PRESENT` | `REVIEW_ONLY` | `PUBLIC_GOVERNANCE` | `NOT_AUTHORIZED_BY_LOCATOR` |
| `LOCAL_ONLY` | 162 | 810 | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `LOCAL_REVIEW_DATA` | `USE_BLOCKED` |
| `LOCAL_ONLY_RESTRICTED` | 3 | 15 | `NOT_ENOUGH_INFORMATION` | `BLOCKED` | `LICENSED_PROVIDER_RESTRICTED` | `USE_BLOCKED` |
| `OFF_HQ_BRANCH_ONLY` | 19 | 95 | `NOT_ENOUGH_INFORMATION` | `BLOCKED` | `LOCAL_REVIEW_DATA` | `USE_BLOCKED` |

Rights/privacy/locality therefore affects 920 rows across 184 artifacts. Direct locator-review rows total 184; the remaining 736 are related missing-link rows for the same artifacts.

## Live HQ

Repository presence proves only locality. Closure still requires exact registered endpoints, an allowed explicit relationship at exact grain, a proof hash, rights/locality result, append-only event, and explicit no-broadening authority/source-use effects. Review-only metadata cannot become production, training, ranking, formula, or display permission.

## Local only

Closure requires an explicit current availability receipt, the existing non-reversible sanitized locator, an exact persistence boundary, no runtime dependency, and no user-facing path. A local path, cache, current file presence, filename, hash alone, or expectation of future persistence is not proof. The six exact authority correspondences remain inactive and cannot close their rows.

## Restricted local only

Closure requires provider/legal evidence and an explicit decision at exact provider, dataset or field-family, purpose, acquisition/license, retention, summary/display, research/training/production, redistribution/export, raw-versus-derived storage, privacy/deletion, attribution, identity-join, expiry, and monitoring grain. No raw content, reversible locator, private identifier, or provider prose is copied into this packet. Model or production permission is never implied.

## Off HQ

The 19 direct audit rows remain canonically `DEFERRED` until an external recovery/admission trigger. Their 76 relationship rows are also execution-ineligible. Recovery, recreation, copying, cherry-picking, migration, or activation requires separate authorization and must preserve the no-recreate link. Git-object existence is not permission.

## Source/use boundary

Source/use decisions, if required, must be explicit at `dataset_id × field_family × purpose × decision_version`. Family-level prose is a routing ceiling, not a decision. The current decision ledger remains empty. Expiry, correction, revocation, or privacy obligations require new append-only supersession or rollback events.
