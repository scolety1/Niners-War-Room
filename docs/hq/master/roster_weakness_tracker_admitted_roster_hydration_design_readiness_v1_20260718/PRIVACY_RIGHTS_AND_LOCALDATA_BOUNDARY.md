# Privacy, Rights, and LocalData Boundary

## Classification

| Data | Class | Repository treatment |
| --- | --- | --- |
| Source registry admission and schema | Public repository governance metadata | Tracked |
| League ID and roster ID | Private league metadata | Local only; redact from docs and UI diagnostics |
| Username, display name, account/user ID | Personal/private metadata | Do not persist unless required; prefer approved opaque team ownership indicator |
| Provider token, credential, cookie, header | Secret | Never read, store, log, fixture, or commit |
| Roster membership and lineup status | Private league data | Approved ignored local root only |
| Transactions and waiver data | Private league activity | Out of V1 hydration scope; do not persist |
| Private messages or arbitrary metadata | Highly private | Prohibited |
| Raw provider payload | Private/source payload | Prohibited from normalized snapshot and receipt; local raw collection is a separately governed lane |
| Licensed data | Rights-controlled | Only under its explicit registry use; no roster-source inference |
| Rights-unresolved source | SOURCE_GATED | No adoption |
| Synthetic fixture | TEST_ONLY | Track only if clearly synthetic and contains no real private IDs |
| Manual Development Lab notes | Private local user content | PRESENTATION_ONLY; outside source truth |

## Rights result

The source registry explicitly admits Sleeper league-state facts and describes the API as free. Repository policy also designates Sleeper as local league-state truth. That is sufficient source-use authority for a bounded local adapter. It does not make raw snapshots public, permit check-in, or establish permission for arbitrary accounts or leagues.

No plugin, local file, provider reachability, platform history, or source name is treated as admission.

## Allowed local root

The existing tracked LocalData contract requires:

- allowedRoot: local_exports;
- noCopy: true;
- noCheckIn: true;
- arbitraryDiskFallback: false.

Future roster snapshots should use a bounded ignored descendant such as local_exports/roster_hydration. The exact path requires implementation review. Existing C:\NWR_SHARED_DATA paths are not automatically adopted and may not be scanned as fallback.

## Storage rules

- Write normalized fields only.
- Store opaque league and roster references locally; do not place raw identifiers in receipts or documentation.
- Exclude usernames and owner IDs unless a narrowly approved mapping is required.
- Do not store credentials, request headers, raw responses, messages, transactions, waiver details, or arbitrary metadata.
- Use immutable snapshot folders or content-addressed files; never overwrite last-known-good.
- Enforce bounded size, closed schema, integrity digest, and safe relative paths.
- Keep snapshots, receipts, backups, quarantine, and deletion tombstones ignored/untracked.

## Fixture rules

- Generate synthetic league, roster, user, and player identifiers.
- Use fictional names or ID-only rows.
- Include duplicate, unresolved, unsupported, stale, corrupt, and missing cases.
- Never derive fixtures by redacting or sampling a private provider payload.
- Mark every fixture SYNTHETIC and TEST_ONLY.

## Deletion and rollback

- User deletion is explicit and scoped to a resolved approved local snapshot root.
- Repository rollback never requires deleting LocalData.
- A snapshot pointer rollback must preserve immutable snapshots and receipts unless the user separately authorizes deletion.
- Never recursively delete a broad or unresolved path.

## Documentation rule

This packet contains no private roster values, league/roster/account IDs, provider payload, LocalData content, or credential material.
