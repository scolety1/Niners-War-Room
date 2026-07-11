# Dependency and Risk Map

## Dependency sequence

```text
Verified inventory
  -> scoped authority ledger
    -> identity assertion registry
      -> versioned schemas and validators
        -> metadata-only read-only workspace
          -> duplicate/conflict/supersession review
            -> typed review queues
              -> parity and rollback validation
                -> optional product-surface design
                  -> separate source/production decisions
```

Formula research, production rookie scoring, inferred UDFA truth, unadmitted source integration, and frozen-comparator use are outside this sequence and remain parked.

## Risk map

| Risk ID | Risk | Evidence | Likelihood | Impact | Control | Owner role | Stop condition |
|---|---|---|---|---|---|---|---|
| R-01 | Duplicate-inflated current population | 157 occurrences / 107 distinct; 50 recurring duplicates | High | High | observation IDs, duplicate ledger, no dedup in loader | identity/artifact steward | a duplicate is silently dropped or counted as a player |
| R-02 | Mixed ID namespaces | numeric Sleeper-like, GSIS, blank under shared field names | High | Critical | opaque NWR ID + namespace aliases | identity steward | provider ID is reused as canonical ID without binding |
| R-03 | Name-based controlling join | existing review pipelines and off-HQ simulation | High | Critical | join-method allowlist; name methods review-only | identity steward | name/name+position creates controlling link |
| R-04 | UDFA inference from absence | 2,514 likely historical; current review status overstates proof | High | High | positive-event model; verified UDFA requires independent admitted evidence | draft evidence steward | missing/not-found becomes undrafted truth |
| R-05 | Source-family default overrides scoped block | CFBD registry entry vs later gates | Medium | Critical | narrowest purpose decision wins, fail closed | source governance | source/model/production status is promoted implicitly |
| R-06 | Provider rights/privacy leakage | CFBD raw cache, RotoWire, restricted matrices, plugin/private receipts | Medium | Critical | sanitized locator only; rights review | rights/privacy owner | raw/substantial/private content enters HQ |
| R-07 | Missing receipt lineage | historical entry, local bridge/labels, current V5 | High | High | failed-lineage queue; metadata-only registration | lineage steward | value is migrated without receipt/as-of/transform proof |
| R-08 | Lifecycle leakage | draft capital treated as pre-draft; current context backfilled historically | Medium | Critical | stage tables and field allowlists | evidence steward | later evidence enters earlier-stage record |
| R-09 | Censoring/missing coerced to miss/zero | incomplete outcome windows; model-lab zero encodings | High | High | explicit availability/censoring/applicability states | outcome steward | unknown/censored becomes numeric zero or miss |
| R-10 | Position-threshold semantic error | 930 QB/TE T24/T36 inapplicable mismatches | High | High | threshold applicability registry | outcome steward | not-applicable threshold used as rookie outcome |
| R-11 | Competing scoring systems merged | 6,700 rank and 3,212 points conflicts | High | Critical | separate scoring-system IDs; conflict ledger | outcome steward | one system silently replaces or averages another |
| R-12 | Competing target systems merged | 1,302 points, 4,922 rank, 2,606 PPG conflicts | High | Critical | separate dataset/window/scoring keys | outcome steward | Formula Mart and Model Lab targets collapse |
| R-13 | Supersession treated as deletion | Gate F versions, draft V1/V2, old labels | Medium | High | append-only supersession and archive policy | artifact steward | predecessor becomes unavailable |
| R-14 | Off-HQ research mistaken for authority | commit 823 ranking simulation and descendants | Medium | Critical | branch/commit locality state and no-recreate index | HQ reviewer | off-HQ rows enter canonical player registry |
| R-15 | Product coupling too early | Compare/Trading/Draft/Data Health already exist | Medium | High | workspace independent; UI later | product owner | scaffold imports or changes app behavior |
| R-16 | Formula lane reopened | sparse/overlay/component artifacts present | Medium | Critical | parked-work list; protected diff scan | Master HQ | formula/model/ranking code or data changes |
| R-17 | Frozen 2026 mutation | immutable comparator packet | Low | Critical | hash and path scan; no workspace dependency | Master HQ | any frozen byte/path changes |
| R-18 | Manifest drift | large inventory and local locators | Medium | High | deterministic manifest, hashes, schema fingerprints | artifact steward | inventory cannot reproduce exactly |
| R-19 | Queue auto-resolution | newer/non-null record appears | Medium | High | closure receipts and allowed resolution proof | queue owner | loader closes/changes authority automatically |
| R-20 | Rollback depends on recreation | source files moved or normalized in place | Low | Critical | additive registry only; originals stay put | migration owner | rollback needs rebuilding source evidence |

## Highest-risk dependencies

Identity and rights are the two hard dependencies. A schema can be built without resolving them, but player-level value consolidation cannot. Outcome parity is the third hard dependency for any later modeling or production use.

## Risk acceptance boundary

The immediate metadata-only scaffold accepts only:

- incomplete metadata explicitly marked as such;
- unresolved identity stored without an NWR binding;
- local/restricted artifacts represented by permitted locators;
- duplicates/conflicts represented without resolution;
- review-only authority retained exactly.

It does not accept value loss, hidden coercion, source promotion, product behavior change, or protected-path mutation.
