# Evidence State and Lifecycle Contract

## State model

Every evidence record stores a primary `evidence_state` plus orthogonal `identity_state`, `source_admission_state`, `use_decision_state`, `availability_state`, `duplication_state`, `locality_state`, and `censoring_state`. The orthogonal fields prevent a primary state from hiding another blocker.

When more than one primary state appears applicable, use this fail-closed precedence:

1. `DUPLICATE_CONFLICTING`
2. `IDENTITY_UNRESOLVED`
3. `SOURCE_UNADMITTED`
4. `USE_BLOCKED`
5. `LOCAL_ONLY_RESTRICTED`
6. `MISSING_EXPECTED`
7. `UNAVAILABLE`
8. `NOT_ENOUGH_INFORMATION`
9. `PROVISIONAL`
10. `DUPLICATE_EQUIVALENT`
11. `SUPERSEDED`
12. `SUPPORTING_EVIDENCE`
13. `CANONICAL_REVIEW_ONLY`
14. `CANONICAL_ADMITTED`

Precedence determines workflow routing, not truth. All dimensions and prior states remain recorded.

## Deterministic state contract

| State | Exact meaning | Permitted uses | Prohibited uses | Display behavior | Review | Supersession | Migration |
|---|---|---|---|---|---|---|---|
| `CANONICAL_ADMITTED` | Current controlling evidence for explicitly named purposes after source, identity, rights, receipt, as-of, and use gates pass. | Only the listed purposes. | Any unlisted purpose; blanket promotion. | Show value, source, as-of, purpose, and caveats. | Re-review on source/schema/use change. | New admitted record appends and supersedes; old remains. | May migrate at field level with full lineage and parity. |
| `CANONICAL_REVIEW_ONLY` | Current controlling review decision or review artifact; not production/model/training truth. | Human review, parity, documentation, bounded research if expressly allowed. | Production, ranking, hidden sort, recommendation, training, source truth unless separately allowed. | Prominent `Review only`; never imply production authority. | Required before stronger use. | Later review version may supersede only the same scope. | Metadata and permitted values may migrate with review-only state intact. |
| `SUPPORTING_EVIDENCE` | Relevant corroborating, lineage, coverage, or independent evidence that does not control authority. | Review, trace, audit, corroboration. | Silent selection as canonical; deletion because another source exists. | Show as supporting and link to authority decision. | Needed if used to change authority. | May be superseded for a narrow purpose, never erased. | Register and preserve relationship; no promotion. |
| `PROVISIONAL` | Evidence is plausible and structured but awaits required confirmation. | Review queue, limited planning, explicit provisional display if allowed. | Confirmed fact, source truth, model/training/production. | `Provisional` plus missing proof and expiry/review date. | Mandatory. | Confirmation creates a new state/decision; original provisional record stays. | Migrate only into provisional area with queue link. |
| `IDENTITY_UNRESOLVED` | The evidence row cannot be bound to one canonical player using durable approved evidence. | Manual identity review; artifact-level inventory. | Player-level joins, aggregation, scoring, training, production. | Preserve source name/ID; no guessed canonical player. | Mandatory identity queue. | Resolution appends an assertion and alias; original row remains. | Register observation with null NWR ID and assertion link. |
| `SOURCE_UNADMITTED` | Source/dataset/field lacks a permitted source-admission decision for the intended use. | Source discovery, rights/receipt review, local retention if separately allowed. | Display/research/model/production/redistribution not expressly allowed. | Show blocker, not value, unless a separate display decision exists. | Source-admission review required. | Admission decision appends; prior blocked state remains historical. | Metadata only; raw/value migration blocked. |
| `USE_BLOCKED` | Source may exist or be admitted for another purpose, but this purpose is explicitly prohibited. | Uses not blocked by the governing decision. | The named blocked purpose. | Show `Use blocked` and governing decision. | Required only to request a new purpose decision. | Later use decision may supersede purpose state only. | Preserve metadata; exclude from blocked-purpose views. |
| `DUPLICATE_EQUIVALENT` | Two or more assertions/files are proven byte- or semantics-equivalent within stated scope. | Retention, lineage, parity, storage review. | Deletion, authority promotion, or silent row collapse. | Show one preferred view only if all copies remain linked. | Human approval before consolidation/archive. | Relationship may be superseded if later differences appear. | Migrate every source assertion or a lossless relationship map. |
| `DUPLICATE_CONFLICTING` | Artifacts or assertions overlap but disagree on identity, value, timing, scoring, applicability, or authority. | Conflict analysis and manual review. | Merge, average, choose winner, score, train, or display as a single fact. | Show competing assertions and conflict reason. | Mandatory conflict queue. | Resolution appends a decision; both source assertions remain. | Migrate as separate observations plus conflict link. |
| `SUPERSEDED` | A documented successor controls the same scope after parity/authority review. | Historical trace, rollback, audit. | Current display/use unless explicitly requested; deletion. | Hide from default current view but show chain. | No new review unless reactivated. | Successor may itself be superseded; chain is append-only. | Preserve with predecessor/successor IDs and hashes. |
| `LOCAL_ONLY_RESTRICTED` | Evidence must remain outside canonical HQ because of rights, privacy, provider-content, receipt-path, or local-authority limits. | Permitted local retention and sanitized aggregate/locator metadata. | Raw copy, substantial excerpts, redistribution, export, or downstream use without decision. | Canonical HQ shows sanitized locator/status only. | Rights/privacy review required for expansion. | New permission appends a decision; original restricted record remains. | Locator/aggregate only unless permitted-use decision explicitly allows more. |
| `MISSING_EXPECTED` | A contract says evidence should exist for this entity/period, but no qualifying observation is present. | Missing-evidence queue and coverage reporting. | Infer zero, false, miss, undrafted, healthy, no-role, or low value. | `Missing expected` with expected source/period. | Review if coverage should change. | Satisfied by a later observation; missing event remains historical. | Migrate queue item and expectation, not a fabricated value. |
| `UNAVAILABLE` | The source or process is known not to provide the evidence for the requested period/query. | Coverage reporting and alternative-source planning. | Treat as blocked, missing error, zero, or negative outcome. | `Unavailable from source` with reason and period. | Only if a new source becomes available. | New availability appends a receipt/version. | Preserve unavailability event; no backfill inference. |
| `NOT_ENOUGH_INFORMATION` | Evidence is insufficient to classify safely and no narrower state fully explains why. | Preserve uncertainty, open research question, blocker reporting. | Guessing, promotion, scoring, source truth, or confident display. | Exact phrase `Not enough information`; list missing proof. | Required if a decision is sought. | New evidence adds a new state; original remains. | Metadata/queue only; never converted to a value. |

## Required non-collapses

- missing draft evidence is not undrafted;
- not found in a draft table is not verified UDFA;
- likely UDFA is not confirmed UDFA;
- `confirmed_udfa_review_only` is not source-truth confirmation;
- unavailable is not blocked;
- blocked is not unavailable;
- provisional is not confirmed;
- normalized-name similarity is not identity confirmation;
- review-only is not production-admitted;
- right-censored is not miss;
- not applicable is not false;
- no history is not zero history;
- local-only is not automatically private, and private/restricted is not automatically admissible locally for every purpose.

## Lifecycle contract

### Pre-draft evidence

Required fields include prospect cycle, evidence date, school stint, declared position, source timestamp, as-of date, and field lineage. College production, testing, measurements, grades, and market context remain separate field families. A prospect grade is not a factual measurement. Current-only market/ADP cannot be projected backward.

### Draft-event evidence

Draft events include drafted status, round, pick, team, supplemental status, transaction/entry event, and evidence-backed undrafted status. Positive draft events can exist even when player identity is unresolved. Absence from a draft dataset creates missing/unknown evidence, not an undrafted event.

### Post-draft/preseason evidence

Roster, contract, depth chart, camp role, injury, and early opportunity require effective timestamps and source freshness. Missing injury is not healthy; missing depth is not no-role; missing snaps is not zero.

### Rookie-season evidence

Usage, games, snaps, touches, targets, points, availability, and finish records carry game/week/season grain and scoring basis. When a source cannot cover a metric, the state is unavailable or missing, not zero.

### Multi-year outcome evidence

Every observation references an `outcome_window_id`, scoring system, threshold applicability, completion state, censoring, and availability rule. Year-two, three-year, five-year, survival, and availability-adjusted outcomes remain separate. Position-inapplicable thresholds are `NOT_APPLICABLE`.

## Current evidence placement decisions

- CFBD player production: `PRE_DRAFT`, `SOURCE_UNADMITTED` for production/model use, review-only identity context where permitted.
- nflverse combine measurements: `PRE_DRAFT`, factual review/display only in current rookie artifacts.
- nflverse positive draft picks: `DRAFT_EVENT`, scoped review-only.
- historical likely-UDFA rows: `DRAFT_EVENT`, `PROVISIONAL` or `NOT_ENOUGH_INFORMATION`.
- current human UDFA decisions: `DRAFT_EVENT`, `CANONICAL_REVIEW_ONLY` decision status, not verified truth.
- current Gate F records: `POST_DRAFT_PRESEASON` display derivatives plus linked draft/pre-draft metadata; not a generic record.
- historical rookie labels: rookie-year fields in `ROOKIE_SEASON`; year-two/3Y/5Y fields in `MULTI_YEAR_OUTCOME`.
- sparse-history research: mixed later-outcome research, not a rookie lifecycle stage.
- off-HQ ranking simulation: `REVIEW_SIMULATION`, local-only/use-blocked.

## State transition requirements

Every transition requires:

- prior record/state ID;
- new evidence or decision ID;
- actor/owner role;
- timestamp;
- permitted transition rule;
- validation receipt;
- affected purpose/fields;
- rollback reference.

No loader may transition evidence based solely on the presence of a newer file or a more favorable value.
