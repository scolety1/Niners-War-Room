# Data Health and refresh acceptance

Data Health/refresh focused coverage passed 116 tests. The final affected route/service suite passed 123 tests after the clean-checkout correction.

Verified receipt contract:

- schema version 2;
- closed top-level and nested schemas;
- exact types and enums;
- recursive duplicate-key rejection;
- secret, provider-payload, and path rejection;
- 2 MiB limit before durable mutation;
- validate-before-mutate transaction;
- rejected writes preserve the complete prior storage state;
- latest attempt, latest success, retained data, stale data, and last-known-good remain distinct.

Refresh Data does not run on route load. The browser matrix created no receipt and did not mutate source/runtime snapshots. Refresh remains an explicit user action; execution adapters, source admission, and freshness thresholds are unchanged.

Settings / Data Health is read-only on inspection. Missing optional full rankings now shows zero rows with a yellow availability caveat rather than silently reading a sibling checkout or falsely presenting the optional source as current. Invalid/corrupt/missing receipts continue to fail closed and do not become trusted state.
