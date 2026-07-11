# Source Admission, Rights, and Privacy Boundary

## Controlling rule

Access is not permission. A plugin, website, API, local cache, user export, recovered file, or public display does not grant persistent retention, canonical copying, display, research, model training, production scoring, redistribution, or export rights.

No source is promoted by this design. Where source-family defaults and later scoped gates differ, the narrowest dataset/field/purpose decision controls and uncertainty fails closed.

## Purpose-specific decision matrix

| Evidence family | Local retention | Canonical HQ summary | Raw receipt storage in HQ | Display | Research | Model training | Production scoring | Redistribution | Export | Current boundary |
|---|---|---|---|---|---|---|---|---|---|---|
| NWR governance packets | Allowed | Allowed | N/A | Allowed as policy | Allowed | N/A | N/A | Repository policy | Allowed | `CANONICAL_ADMITTED` for policy only |
| nflverse completed draft picks | Allowed with receipt | Allowed metadata/positive facts under scoped gate | Allowed only with permitted receipt policy | Review/display facts where approved | Bounded review | Blocked in current rookie artifacts | Blocked | Upstream license/policy required | Receipt-safe export only | Positive drafted evidence only; absence is unknown |
| nflverse combine | Allowed with receipt | Metadata/coverage allowed | Receipt decision required | Factual review/display only in current lane | Bounded review | Blocked | Blocked | Upstream policy required | Receipt-safe only | Partial current coverage; grades excluded |
| nflverse player stats / Outcome V2 derivations | Allowed | Tracked compact review source and summaries allowed | Existing permitted receipts only | Review/display where separately approved | Review/parity | Blocked for rookie training | Blocked | Upstream/derived policy required | Purpose-limited | Multiple scoring systems remain separate |
| Official NFL draft results | Candidate admitted factual family | Summary/positive facts after receipt | Field/source receipt required | Review/display after identity gate | Review | Separate decision required | Separate decision required | Official terms apply | Separate decision | No new source was acquired here |
| Tankathon completed-results verification | Local verification if permitted | Aggregate verification note | Raw copy not assumed | Verification context after cross-check | Review only | Blocked | Blocked | Not assumed | Blocked absent decision | Never use mock/big-board as draft truth |
| CFBD API raw cache | Existing local retention only | Aggregate coverage and sanitized metadata | Blocked pending rights/receipt decision | Blocked except existing authorized review context | Identity/coverage review only | Blocked | Blocked | Blocked pending terms | Blocked | `SOURCE_UNADMITTED` for downstream use |
| CFBD identity assertions | Allowed | Decision/queue metadata allowed | Raw source rows remain governed by CFBD boundary | Review-only | Identity research only | Blocked | Blocked | Blocked | Sanitized decisions only | Human approval does not grant source truth |
| NFLVerse current depth/roster/injury context | Allowed with receipts | Summary allowed | Dataset receipt decision required | Existing display-only contexts | Bounded review | Historical use blocked absent point-in-time receipts | Blocked | Upstream policy | Purpose-limited | Current context cannot be backfilled historically |
| Local rookie GSIS bridge/labels | Existing local retention | Hash, schema, counts, lineage summary allowed | Raw copy deferred | Review-only if separately surfaced | Review/evaluation | Blocked | Blocked | Blocked absent derived-data decision | Metadata only now | Local-only, review-only, incomplete tracked receipt chain |
| Historical Fantasy Finish Foundation | Existing local retention | Aggregate/hash/conflict summary allowed | Raw copy deferred | Not newly authorized | Independent parity review | Blocked | Blocked | Upstream/derived policy | Metadata only | Conflicts with Outcome V2 |
| Historical Model Lab | Existing local retention | Aggregate/hash/conflict summary allowed | Raw copy deferred | Not newly authorized | Parked review research | Blocked | Blocked | Blocked | Metadata only | Formula research paused; missing values encoded as zeros must not migrate as evidence |
| RotoWire factual user exports | Subject to license/user entitlement | Aggregate metadata only | Raw copy blocked unless contract permits | Existing licensed factual display only where admitted | Local review if permitted | Separate contract/admission required | Blocked | Non-redistributable absent permission | Blocked | Subscription/provider content is local-only restricted |
| PlayerProfiler factual profiles | Subject to license/export terms | Field-level summary after admission | Raw copy not assumed | Existing admitted factual context only | Review if permitted | Separate field decision | Blocked | Not assumed | Blocked absent decision | Rankings/ADP/values remain display-only/blocked |
| Prospect grades, ranks, projections, profile text | Local retention only if lawfully obtained | Blocker/status only | Blocked | Blocked absent explicit grade/display decision | Source discovery only | Blocked | Blocked | Blocked | Blocked | ESPN/NFL.com/PFF/third-party grade provenance/rights unresolved |
| JackLich10 / array-carpenter draft datasets | Existing reference only | Source-candidate status | Blocked | Blocked | Rights review only | Blocked | Blocked | Blocked | Blocked | No clear repository license found in prior audit |
| FootballDB | Manual spot-check only if explicitly directed | No substantial content | No | No automated display/collection | Manual source check only | Blocked | Blocked | Blocked | Blocked | Automated collection is explicitly blocked |
| Current market/ADP/ECR | Existing current display context | Current metadata summary | Existing receipt policy | Display-only | Current review only | Blocked | Blocked | Provider terms | Blocked absent decision | Cannot be used historically |
| Recovered prospect matrices | Existing restricted local retention | Sanitized locator/hash/status only | Never copy raw without decision | Blocked | Blocked except rights/identity audit | Blocked | Blocked | Blocked | Blocked | Embedded provider content, unclear rights, normalized-name identity |
| Flaim/FantasyBot/plugin outputs | Original restricted archive only | Sanitized aggregate conclusions already canonical | Raw/private receipts blocked | No persistent panel/adapter | Manual consultation only with caveats/terms | Blocked | `0%` influence | Blocked | Blocked | Do not call or reopen research |
| Private league, roster, transaction, owner, account data | Restricted local evidence only when authorized | Sanitized aggregate only | Blocked | Blocked unless explicit product need and consent | Blocked by default | Blocked | Blocked | Never | Never | No private identifiers or reversible keys in HQ |

## Normalized family-level decision ledger

The narrative matrix above explains caveats; it is not machine-interpreted. The normalized routing values below use only the six `SOURCE_USE_DECISION_LEDGER` decision values. A later scaffold must create one versioned row per `(dataset_id, field_family, purpose)` for all nine purposes and link its approval receipt. Until that dataset/field row exists, the family value is only a fail-closed routing ceiling and cannot admit a use. `NOT_ENOUGH_INFORMATION` never means allowed.

| Evidence family | LOCAL_RETENTION | CANONICAL_HQ_SUMMARY | RAW_RECEIPT_STORAGE | DISPLAY | RESEARCH | MODEL_TRAINING | PRODUCTION_SCORING | REDISTRIBUTION | EXPORT |
|---|---|---|---|---|---|---|---|---|---|
| NWR governance packets | `ALLOWED` | `ALLOWED` | `NOT_APPLICABLE` | `ALLOWED` | `ALLOWED` | `NOT_APPLICABLE` | `NOT_APPLICABLE` | `ALLOWED_WITH_CAVEATS` | `ALLOWED` |
| nflverse completed draft picks | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` |
| nflverse combine | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `NOT_ENOUGH_INFORMATION` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` |
| nflverse player stats / Outcome V2 derivations | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` |
| Official NFL draft results | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `REVIEW_ONLY` | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` |
| Tankathon completed-results verification | `REVIEW_ONLY` | `ALLOWED_WITH_CAVEATS` | `NOT_ENOUGH_INFORMATION` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| CFBD API raw cache | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| CFBD identity assertions | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `ALLOWED_WITH_CAVEATS` |
| NFLVerse current depth/roster/injury context | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `NOT_ENOUGH_INFORMATION` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` |
| Local rookie GSIS bridge/labels | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `ALLOWED_WITH_CAVEATS` |
| Historical Fantasy Finish Foundation | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` |
| Historical Model Lab | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| RotoWire factual user exports | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `REVIEW_ONLY` | `REVIEW_ONLY` | `NOT_ENOUGH_INFORMATION` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| PlayerProfiler factual profiles | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `NOT_ENOUGH_INFORMATION` | `REVIEW_ONLY` | `REVIEW_ONLY` | `NOT_ENOUGH_INFORMATION` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `BLOCKED` |
| Prospect grades, ranks, projections, profile text | `NOT_ENOUGH_INFORMATION` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| JackLich10 / array-carpenter draft datasets | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| FootballDB | `REVIEW_ONLY` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| Current market/ADP/ECR | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `REVIEW_ONLY` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `NOT_ENOUGH_INFORMATION` | `BLOCKED` |
| Recovered prospect matrices | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| Flaim/FantasyBot/plugin outputs | `ALLOWED_WITH_CAVEATS` | `ALLOWED_WITH_CAVEATS` | `BLOCKED` | `BLOCKED` | `REVIEW_ONLY` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |
| Private league, roster, transaction, owner, account data | `ALLOWED_WITH_CAVEATS` | `NOT_ENOUGH_INFORMATION` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` | `BLOCKED` |

The narrowest legal/privacy, dataset, field, identity, receipt, and purpose decision may only make a family ceiling more restrictive. It cannot make it more permissive. The implementation lane must reject free-text or missing decision values rather than infer them.

## Source categories

### Admitted only within a narrow scope

- NWR governance and no-recreate decisions;
- nflverse positive completed draft facts for existing review-only rookie artifacts;
- nflverse factual combine measurements for existing review/display review scope;
- Outcome V2 compact labels for tracked review/parity scope;
- existing display contexts through their own current gates.

An admitted source family does not imply admitted model, training, production, redistribution, or export use.

### Review-only

- current CFBD human identity decisions;
- historical entry-status snapshot;
- local GSIS bridge and 919-row labels;
- current UDFA human review decisions;
- Gate E/F and draft-capital sidecars;
- sparse-history and Formula Data Mart research;
- independent historical outcome systems.

### Restricted or local-only

- raw CFBD caches pending rights/receipt decision;
- RotoWire and other licensed provider exports;
- recovered prospect matrices and component rows;
- local shared-data outputs not yet approved for canonical raw retention;
- off-HQ ranking simulation and manual-recovery sources;
- plugin/private archives.

### Unclear rights or missing receipts

- third-party combine/prospect repositories without clear licenses;
- prospect grades, profile text, and analyst-mediated fields;
- CFBD raw redistribution/persistent downstream use;
- local bridge/labels whose tracked manifests omit complete input hashes/receipt evidence;
- historical entry artifact with no tracked builder/input lineage;
- recovered files whose provider/output rights are unclear.

## Privacy classes

| Class | Examples | Canonical handling |
|---|---|---|
| `PUBLIC_GOVERNANCE` | NWR policy, public source descriptions | Full text allowed |
| `PUBLIC_FACTUAL_RECEIPT` | permitted nflverse receipt metadata | Store required receipt fields and hashes |
| `LOCAL_REVIEW_DATA` | shared rookie bridge/labels, local research outputs | Store metadata/hash; raw copy only after retention decision |
| `LICENSED_PROVIDER_RESTRICTED` | RotoWire, paid/provider exports | Sanitized locator/aggregate only unless contract permits |
| `PRIVATE_USER_OR_LEAGUE` | owner, roster, account, transaction, draft identifiers | Exclude raw/reversible identifiers from HQ |
| `CREDENTIAL_SECRET` | API keys, cookies, OAuth/session tokens | Never store in evidence workspace |

## Canonical exclusion list

Do not copy into canonical HQ without a permitted-use decision:

- raw provider JSON or substantial provider output;
- exact private/local receipt paths where the path itself is restricted;
- league, owner, roster, transaction, draft, or account identifiers;
- credentials, headers, cookies, tokens, or session data;
- provider-generated explanations or proprietary prose;
- restricted prospect JSON fields embedded in recovered matrices;
- unlicensed grades, ranks, projections, or profile text;
- player rows from a local-only artifact merely because a hash is known.

Use a sanitized `restricted_locator_id`, aggregate counts, a rights state, and the minimum permitted integrity metadata.

## Rights-review proof required

Before expanding a source's use, a human decision must state:

- provider and exact dataset/field family;
- acquisition method and account/license context;
- retention permission;
- display permission;
- research/model/training/production permission separately;
- redistribution/export permission;
- whether raw receipts or only derived facts may be stored;
- private-data handling and deletion obligations;
- citation/attribution requirements;
- permitted identity joins;
- expiration/change-monitoring rule;
- signed decision receipt or other authoritative approval.

Silence, public visibility, an API response, a local cache, or prior manual use is not proof.

## Governance precedence

Use this order, narrowest first:

1. legal/privacy prohibition;
2. explicit dataset/field/purpose decision;
3. source receipt and license decision;
4. identity and as-of gate;
5. source-family default;
6. discovery/reference status.

Any unresolved conflict results in `NOT_ENOUGH_INFORMATION`, `SOURCE_UNADMITTED`, `USE_BLOCKED`, or `LOCAL_ONLY_RESTRICTED`, whichever is more specific.
