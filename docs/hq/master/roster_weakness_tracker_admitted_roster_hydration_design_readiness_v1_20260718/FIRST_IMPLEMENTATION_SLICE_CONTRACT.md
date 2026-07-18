# First Implementation Slice Contract

## Authorization

NOT AUTHORIZED while the verdict remains blocked.

## Earliest eligible slice after re-entry

Typed read-only roster snapshot contract and exact-identity validator, using synthetic fixtures only.

## Allowed paths

Exact paths require a new work order. A bounded proposal may include:

- one new roster snapshot model/service under src, without provider access;
- one synthetic fixture family under tests/fixtures;
- focused unit tests under tests;
- documentation under a new approved packet.

No existing path is pre-authorized by this design packet.

## Allowed behavior

- parse a normalized synthetic snapshot;
- validate closed fields, enums, timestamps, duplicate keys, and integrity;
- exact-join a declared Sleeper source ID to a unique NWR player ID;
- emit validation and coverage results in memory;
- fail closed on missing, duplicate, unsupported, corrupt, gated, or partial input;
- perform no writes except test-temporary output.

## Prohibited behavior

- provider or network calls;
- production roster hydration;
- LocalData discovery outside an explicit passed path;
- application route or page wiring;
- changes to current roster, league, identity, source, rank, formula, recommendation, refresh, Data Health, or Decision Trust behavior;
- name-based joins or fallbacks;
- snapshot persistence or latest-pointer mutation;
- weakness calculations;
- recommendations, sorting, ranking, or advice.

## Exit criteria

- all re-entry evidence accepted;
- exact-ID tests cover every in-scope asset and all failure states;
- no unresolved asset is silently dropped;
- clean-checkout tests pass with synthetic fixtures;
- LocalData tier reports separately and truthfully;
- protected/frozen and primary-worktree preservation checks pass;
- separately reviewed implementation work order authorizes exact paths.

Later slices are not automatically authorized.
