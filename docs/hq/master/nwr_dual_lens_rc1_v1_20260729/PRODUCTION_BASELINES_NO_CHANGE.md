# Production baselines no-change proof

Finished V1 SHA-256 remains `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4` with 240 rows and the
required top five. Frozen comparator SHA-256 remains
`b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179` with 924 rows. Outcome V3 current-board SHA-256
remains `279cd23942e5f5ebd94543c44ffaf03d76a018e6e9bc9ce4e74f9bebd1fb891d` and its schema remains 79 rows.

The builder's only write root is this research packet. No app, source service,
runtime state, local export, frozen comparator, Finished V1, or Outcome V3 path
is a target. Production identifier `NWR_FINISHED_VERSION_1` remains authoritative.
