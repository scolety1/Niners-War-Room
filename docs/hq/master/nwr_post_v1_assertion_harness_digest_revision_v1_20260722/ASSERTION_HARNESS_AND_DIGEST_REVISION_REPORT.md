# Assertion harness and digest revision report

Verdict: `GREEN_NWR_POST_V1_ASSERTION_HARNESS_REVISION_READY_FOR_ADOPTION`

Starting HQ `532215c1b1a8896d5a838b827535c13dd655199d` and tree
`bca7ca6ecc1111ead8289a77650f481516d283fd` were verified after fetch/prune.
The exact source chain is HQ -> `c0b3a136d3fdbb247cd702cbc7b7300676bda859`
-> `18c63e969905e3218cfdc127551b5b55afae6201`. The rejected evidence-only
commit `c4d52d72972682c946c37a18e061c07d09ff66ac` was inspected but not adopted.

The revision replaces source-literal acceptance with execution of the production
`/` route in an isolated structural renderer. It captures the real page's H1,
tile headings, badges, body text, and links; resolves every target through
`app.navigation`; and binds disposition checks to the pre-existing 60-route audit
authority rather than adding a second per-route table.

The page-open harness records before/after directory and file-hash inventories and
instruments write-capable filesystem, receipt, draft/runtime, Development Lab,
refresh, launcher, dataframe-export, and SQLite boundaries. Normal Start Here
rendering produces `DURABLE_MUTATION_COUNT = 0`. Harmless in-memory session state
is allowed. All required durable mutations are detected in temporary state only.

The two legacy state aggregates have no repository-recorded serializer or exact
command and are retained only as `LEGACY_AGGREGATE_METHOD_NOT_REPRODUCIBLE`. The
new `PERSISTENT_STATE_DIGEST_V1` uses canonical metadata-only UTF-8 JSON. It yields
`88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`
for the 14-file persistent inventory and
`1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`
for the 7-file recovery inventory.

No application, routing, page-copy, formula, rank, score, source, identity,
persistent-state, launcher, or production-data file changed.
